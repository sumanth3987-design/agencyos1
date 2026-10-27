import logging
import os

import requests
import razorpay

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db, get_razorpay_client
from app.models import Project, Payment, PACKAGE_PRICES, get_ist_now
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

logger = logging.getLogger(__name__)

payments_bp = Blueprint("payments", __name__)
razorpay_client = get_razorpay_client()
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")

@payments_bp.route(
    "/payment/create-order/<int:project_id>",
    methods=["POST"]
)
@login_required
def create_payment_order(project_id):

    if current_user.role != "customer":

        return jsonify({
            "success": False,
            "message": "Customer access required."
        }), 403

    if razorpay_client is None:

        return jsonify({
            "success": False,
            "message": "Payment service unavailable."
        }), 503

    project = Project.query.filter_by(
        id=project_id,
        customer_id=current_user.id
    ).first()

    if not project:

        return jsonify({
            "success": False,
            "message": "Project not found."
        }), 404

    amount = PACKAGE_PRICES.get(
        project.package
    )

    if not amount:

        return jsonify({
            "success": False,
            "message": "Invalid package amount."
        }), 400

    existing_paid_payment = (
        Payment.query
        .filter_by(
            project_id=project.id,
            customer_id=current_user.id,
            status="Paid"
        )
        .first()
    )

    if existing_paid_payment:

        return jsonify({
            "success": False,
            "message": "This project has already been paid."
        }), 400

    if project.status not in ("Payment Pending", "Pending Assignment"):

        return jsonify({
            "success": False,
            "message": "Project is not in a payable state."
        }), 400

    amount_paise = int(
        amount * 100
    )

    # Idempotency: reuse a still-open local order instead of creating
    # duplicate Razorpay orders for the same project/customer.
    existing_active_payment = (
        Payment.query
        .filter_by(
            project_id=project.id,
            customer_id=current_user.id,
            status="Created",
        )
        .order_by(Payment.created_at.desc())
        .first()
    )

    if (
        existing_active_payment is not None
        and existing_active_payment.razorpay_order_id
        and existing_active_payment.amount == amount
    ):

        return jsonify({
            "success": True,
            "order_id": existing_active_payment.razorpay_order_id,
            "amount": amount_paise,
            "currency": "INR",
            "key_id": RAZORPAY_KEY_ID,
        })

    try:

        order = razorpay_client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "receipt": f"agencyos_project_{project.id}",
            "notes": {
                "project_id": str(project.id),
                "customer_id": str(current_user.id)
            }
        })

    except (
        razorpay.errors.BadRequestError,
        razorpay.errors.GatewayError,
        razorpay.errors.ServerError,
        razorpay.errors.SignatureVerificationError,
        requests.exceptions.RequestException,
        ConnectionError,
        TimeoutError,
        OSError,
    ) as exc:
        logger.error(
            "Razorpay order creation failed: %s",
            type(exc).__name__,
        )
        return jsonify({
            "success": False,
            "message": "Unable to create Razorpay order."
        }), 500

    # Prevent duplicate Razorpay order IDs from being recorded locally.
    existing_order_payment = Payment.query.filter_by(
        razorpay_order_id=order["id"]
    ).first()

    if existing_order_payment is not None:

        if (
            existing_order_payment.project_id == project.id
            and existing_order_payment.customer_id == current_user.id
            and existing_order_payment.status == "Created"
            and existing_order_payment.amount == amount
        ):

            return jsonify({
                "success": True,
                "order_id": existing_order_payment.razorpay_order_id,
                "amount": amount_paise,
                "currency": "INR",
                "key_id": RAZORPAY_KEY_ID,
            })

        return jsonify({
            "success": False,
            "message": "Payment order already exists."
        }), 400

    payment = Payment(
        project_id=project.id,
        customer_id=current_user.id,
        razorpay_order_id=order["id"],
        amount=amount,
        currency="INR",
        status="Created"
    )

    try:

        db.session.add(
            payment
        )

        db.session.commit()

    except IntegrityError:

        db.session.rollback()

        existing_active_payment = (
            Payment.query
            .filter_by(
                project_id=project.id,
                customer_id=current_user.id,
                status="Created",
            )
            .order_by(Payment.created_at.desc())
            .first()
        )

        if (
            existing_active_payment is not None
            and existing_active_payment.razorpay_order_id
            and existing_active_payment.amount == amount
        ):

            return jsonify({
                "success": True,
                "order_id": existing_active_payment.razorpay_order_id,
                "amount": amount_paise,
                "currency": "INR",
                "key_id": RAZORPAY_KEY_ID,
            })

        existing_order_payment = Payment.query.filter_by(
            razorpay_order_id=order["id"]
        ).first()

        if (
            existing_order_payment is not None
            and existing_order_payment.project_id == project.id
            and existing_order_payment.customer_id == current_user.id
            and existing_order_payment.status == "Created"
            and existing_order_payment.amount == amount
        ):

            return jsonify({
                "success": True,
                "order_id": existing_order_payment.razorpay_order_id,
                "amount": amount_paise,
                "currency": "INR",
                "key_id": RAZORPAY_KEY_ID,
            })

        return jsonify({
            "success": False,
            "message": "Unable to create payment order."
        }), 400

    except SQLAlchemyError as exc:

        db.session.rollback()

        logger.error(
            "Payment order database write failed: %s",
            type(exc).__name__,
        )

        return jsonify({
            "success": False,
            "message": "Unable to create payment order."
        }), 500

    return jsonify({
        "success": True,
        "order_id": order["id"],
        "amount": amount_paise,
        "currency": "INR",
        "key_id": RAZORPAY_KEY_ID
    })


# =========================================================
# VERIFY RAZORPAY PAYMENT
# =========================================================

@payments_bp.route(
    "/payment/verify",
    methods=["POST"]
)
@login_required
def verify_payment():

    if current_user.role != "customer":

        return jsonify({
            "success": False,
            "message": "Customer access required."
        }), 403

    if razorpay_client is None:

        return jsonify({
            "success": False,
            "message": "Payment service unavailable."
        }), 503

    data = request.get_json(
        silent=True
    ) or {}

    razorpay_order_id = data.get(
        "razorpay_order_id",
        ""
    ).strip()

    razorpay_payment_id = data.get(
        "razorpay_payment_id",
        ""
    ).strip()

    razorpay_signature = data.get(
        "razorpay_signature",
        ""
    ).strip()

    if not (
        razorpay_order_id
        and razorpay_payment_id
        and razorpay_signature
    ):

        return jsonify({
            "success": False,
            "message": "Missing payment verification data."
        }), 400

    payment = (
        Payment.query
        .filter_by(
            razorpay_order_id=razorpay_order_id,
            customer_id=current_user.id
        )
        .first()
    )

    if not payment:

        return jsonify({
            "success": False,
            "message": "Payment record not found."
        }), 404

    # Prevent the same Razorpay payment ID from being applied to more
    # than one local payment record.
    duplicate_payment = (
        Payment.query
        .filter(
            Payment.razorpay_payment_id == razorpay_payment_id,
            Payment.id != payment.id,
        )
        .first()
    )

    if duplicate_payment is not None:

        return jsonify({
            "success": False,
            "message": "Payment ID already used."
        }), 400

    # Idempotency: already-paid payments return success without
    # re-calling Razorpay or mutating state on repeat callbacks.
    if payment.status == "Paid":

        return jsonify({
            "success": True,
            "message": "Payment already verified.",
            "project_id": payment.project_id
        })

    if payment.status != "Created":

        return jsonify({
            "success": False,
            "message": "Payment is not in a verifiable state."
        }), 400

    project = Project.query.filter_by(
        id=payment.project_id,
        customer_id=current_user.id
    ).first()

    if not project:

        return jsonify({
            "success": False,
            "message": "Project not found."
        }), 404

    if project.status not in ("Payment Pending", "Pending Assignment"):

        return jsonify({
            "success": False,
            "message": "Project is not in a payable state."
        }), 400

    try:

        razorpay_client.utility.verify_payment_signature({
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature
        })

    except (
        razorpay.errors.SignatureVerificationError,
        razorpay.errors.BadRequestError,
        razorpay.errors.GatewayError,
        razorpay.errors.ServerError,
        requests.exceptions.RequestException,
        ConnectionError,
        TimeoutError,
        OSError,
    ) as exc:
        logger.warning(
            "Razorpay signature verification failed: %s",
            type(exc).__name__,
        )
        return jsonify({
            "success": False,
            "message": "Payment signature verification failed."
        }), 400


    try:

        razorpay_order = (
            razorpay_client.order.fetch(
                razorpay_order_id
            )
        )

        razorpay_payment = (
            razorpay_client.payment.fetch(
                razorpay_payment_id
            )
        )

    except (
        razorpay.errors.BadRequestError,
        razorpay.errors.GatewayError,
        razorpay.errors.ServerError,
        razorpay.errors.SignatureVerificationError,
        requests.exceptions.RequestException,
        ConnectionError,
        TimeoutError,
        OSError,
    ) as exc:
        logger.error(
            "Razorpay payment fetch failed: %s",
            type(exc).__name__,
        )
        return jsonify({
            "success": False,
            "message":
                "Unable to verify payment with Razorpay."
        }), 500

    expected_amount = int(
        payment.amount * 100
    )

    actual_order_amount = int(
        razorpay_order.get(
            "amount",
            0
        )
    )

    actual_payment_amount = int(
        razorpay_payment.get(
            "amount",
            0
        )
    )

    order_currency = (
        razorpay_order.get(
            "currency"
        )
    )

    payment_currency = (
        razorpay_payment.get(
            "currency"
        )
    )

    captured = (
        razorpay_payment.get(
            "status"
        )
        == "captured"
    )

    order_id_matches = (
        razorpay_order.get("id") == razorpay_order_id
        and razorpay_payment.get("order_id") == razorpay_order_id
        and razorpay_order_id == payment.razorpay_order_id
    )

    amount_valid = (
        actual_order_amount
        == expected_amount
        and actual_payment_amount
        == expected_amount
    )

    currency_valid = (
        order_currency == payment.currency
        and payment_currency == payment.currency
        and payment.currency == "INR"
    )

    if not (
        captured
        and order_id_matches
        and amount_valid
        and currency_valid
    ):

        return jsonify({
            "success": False,
            "message":
                "Payment verification failed."
        }), 400

    try:

        updated_rows = (
            Payment.query
            .filter_by(
                id=payment.id,
                status="Created"
            )
            .update(
                {
                    "razorpay_payment_id": razorpay_payment_id,
                    "status": "Paid",
                    "paid_at": get_ist_now(),
                },
                synchronize_session=False
            )
        )

        if updated_rows != 1:

            db.session.rollback()

            refreshed_payment = Payment.query.get(
                payment.id
            )

            if refreshed_payment and refreshed_payment.status == "Paid":

                return jsonify({
                    "success": True,
                    "message": "Payment already verified.",
                    "project_id": refreshed_payment.project_id
                })

            return jsonify({
                "success": False,
                "message": "Payment verification failed."
            }), 400

        Project.query.filter_by(
            id=project.id
        ).update(
            {"status": "Pending Assignment"},
            synchronize_session=False
        )

        db.session.commit()

    except IntegrityError:

        db.session.rollback()

        refreshed_payment = Payment.query.get(
            payment.id
        )

        if refreshed_payment and refreshed_payment.status == "Paid":

            return jsonify({
                "success": True,
                "message": "Payment already verified.",
                "project_id": refreshed_payment.project_id
            })

        duplicate_payment = (
            Payment.query
            .filter(
                Payment.razorpay_payment_id == razorpay_payment_id,
                Payment.id != payment.id,
            )
            .first()
        )

        if duplicate_payment is not None:

            return jsonify({
                "success": False,
                "message": "Payment ID already used."
            }), 400

        return jsonify({
            "success": False,
            "message": "Payment verification failed."
        }), 400

    except SQLAlchemyError as exc:

        db.session.rollback()

        logger.error(
            "Payment verification database write failed: %s",
            type(exc).__name__,
        )

        return jsonify({
            "success": False,
            "message": "Payment verification failed."
        }), 500

    return jsonify({
        "success": True,
        "message": "Payment verified successfully.",
        "project_id": project.id
    })


# =========================================================
# PAYMENT PAGE
# =========================================================

@payments_bp.route(
    "/payment/<int:project_id>"
)
@login_required
def payment_page(project_id):

    if current_user.role != "customer":

        return redirect(
            url_for("dashboard")
        )

    project = Project.query.filter_by(
        id=project_id,
        customer_id=current_user.id
    ).first()

    if not project:

        flash(
            "Project not found."
        )

        return redirect(
            url_for("dashboard")
        )

    amount = PACKAGE_PRICES.get(
        project.package,
        0
    )

    payment = (
        Payment.query
        .filter_by(
            project_id=project.id,
            customer_id=current_user.id
        )
        .order_by(
            Payment.created_at.desc()
        )
        .first()
    )

    if payment and payment.status == "Paid":

        return redirect(
            url_for(
                "project_details",
                project_id=project.id
            )
        )

    return render_template(
        "payment.html",
        project=project,
        amount=amount,
        razorpay_key_id=RAZORPAY_KEY_ID
    )


# =========================================================
# SERVICES API
# =========================================================


