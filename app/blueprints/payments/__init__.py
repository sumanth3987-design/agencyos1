from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db, get_razorpay_client
from app.models import Project, Payment, PACKAGE_PRICES, get_ist_now
import os

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

    amount_paise = int(
        amount * 100
    )

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

    except Exception as e:

        print(
            "Razorpay order creation error:",
            repr(e)
        )

        return jsonify({
            "success": False,
            "message":
                "Unable to create Razorpay order."
        }), 500

    payment = Payment(
        project_id=project.id,
        customer_id=current_user.id,
        razorpay_order_id=order["id"],
        amount=amount,
        currency="INR",
        status="Created"
    )

    db.session.add(
        payment
    )

    db.session.commit()

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

    project = Project.query.filter_by(
        id=payment.project_id,
        customer_id=current_user.id
    ).first()

    if not project:

        return jsonify({
            "success": False,
            "message": "Project not found."
        }), 404

    try:

        razorpay_client.utility.verify_payment_signature({
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature
        })

    except Exception as e:

        print(
            "Razorpay signature verification error:",
            repr(e)
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

    except Exception as e:

        print(
            "Razorpay payment fetch error:",
            repr(e)
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
        razorpay_payment.get(
            "order_id"
        )
        == razorpay_order_id
    )

    amount_valid = (
        actual_order_amount
        == expected_amount
        and actual_payment_amount
        == expected_amount
    )

    currency_valid = (
        order_currency == "INR"
        and payment_currency == "INR"
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

    payment.razorpay_payment_id = (
        razorpay_payment_id
    )

    payment.status = "Paid"

    payment.paid_at = get_ist_now()

    project.status = "Pending Assignment"

    db.session.commit()

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


