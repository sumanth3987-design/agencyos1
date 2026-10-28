import logging

import hashlib
import secrets
from datetime import timedelta
from urllib.parse import urljoin, urlparse

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, csrf, limiter
from app.services.email import send_email, EmailDeliveryError

from app.models import User, CustomerProfile, ProfessionalProfile, UserToken, get_ist_now

auth_bp = Blueprint("auth", __name__)

logger = logging.getLogger(__name__)

def _hash_token(raw_token):
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def _validate_password_policy(password):
    """Return whether a password satisfies the shared AgencyOS policy."""
    return (
        isinstance(password, str)
        and 8 <= len(password) <= 128
        and any(char.isalpha() for char in password)
        and any(char.isdigit() for char in password)
    )


def _trusted_external_url(endpoint, **values):
    """Build an absolute URL using a trusted configured application origin.

    Falling back to Flask's request-derived external URL keeps local
    development and tests working when ``APP_BASE_URL`` is not configured.
    """
    path = url_for(endpoint, _external=False, **values)
    base_url = (current_app.config.get("APP_BASE_URL") or "").strip()
    if base_url:
        parsed = urlparse(base_url)
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            return urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
    return url_for(endpoint, _external=True, **values)


def _create_user_token(user, purpose, expires_at):
    raw_token = secrets.token_urlsafe(32)
    token = UserToken(
        user_id=user.id,
        purpose=purpose,
        token_hash=_hash_token(raw_token),
        expires_at=expires_at,
    )
    db.session.add(token)
    db.session.commit()
    return raw_token


def _get_valid_token(raw_token, purpose):
    if not raw_token:
        return None
    token = UserToken.query.filter_by(
        token_hash=_hash_token(raw_token),
        purpose=purpose,
    ).first()
    if token is None or token.used_at is not None:
        return None

    expires_at = token.expires_at
    if expires_at.tzinfo is not None:
        expires_at = expires_at.replace(tzinfo=None)

    now = get_ist_now()
    if now.tzinfo is not None:
        now = now.replace(tzinfo=None)

    if expires_at <= now:
        return None
    return token


def _consume_token(token):
    updated = (
        UserToken.query
        .filter_by(id=token.id, used_at=None)
        .update({"used_at": get_ist_now()}, synchronize_session=False)
    )
    db.session.commit()
    return updated == 1


# CSRF tokens are required for state-changing requests on authenticated
# sessions (e.g. POST /logout). Login and registration endpoints are
# excluded because they are the initial authentication steps used by
# anonymous visitors before a session exists.

@auth_bp.route("/")
def index():

    return render_template(
        "index.html"
    )


def _issue_email_verification(user):
    expires_at = get_ist_now() + timedelta(
        hours=current_app.config.get(
            "EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS", 24
        )
    )
    raw_token = _create_user_token(
        user, "email_verification", expires_at
    )
    verification_link = _trusted_external_url(
        "verify_email", token=raw_token
    )
    try:
        send_email(
            user.email,
            "Verify your AgencyOS email address",
            "Verify your email address:\n\n%s" % verification_link,
        )
    except EmailDeliveryError:
        logger = logging.getLogger(__name__)
        logger.error(
            "Email verification delivery failed for user %s",
            user.id,
        )



# =========================================================
# CUSTOMER / PROFESSIONAL REGISTER
# =========================================================


@auth_bp.route(
    "/register",
    methods=["GET", "POST"]
)
@csrf.exempt
@limiter.limit("5 per hour")
def register():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        account_type = request.form.get(
            "account_type",
            "customer"
        ).strip().lower()

        # -------------------------------------------------
        # BASIC VALIDATION
        # -------------------------------------------------

        if not name or not email or not password:

            flash(
                "Please fill all required fields."
            )

            return redirect(
                url_for("register")
            )

        if not _validate_password_policy(password):

            flash(
                "Password must be 8-128 characters and "
                "include both letters and numbers."
            )

            return redirect(
                url_for("register")
            )

        # -------------------------------------------------
        # ONLY CUSTOMER / PROFESSIONAL ALLOWED
        # -------------------------------------------------

        if account_type not in (
            "customer",
            "professional"
        ):

            flash(
                "Please select a valid account type."
            )

            return redirect(
                url_for("register")
            )

        # -------------------------------------------------
        # CHECK EMAIL + ROLE
        # -------------------------------------------------

        existing_user = User.query.filter_by(
            email=email,
            role=account_type
        ).first()

        if existing_user:

            flash(
                "Registration could not be completed. "
                "Please try a different email or log in."
            )

            return redirect(
                url_for("register")
            )

        # =================================================
        # PROFESSIONAL REGISTRATION
        # =================================================

        if account_type == "professional":

            expertise_values = [
            item.strip()
            for item in request.form.getlist("expertise")
            if item.strip()
            ]

            expertise = ", ".join(expertise_values)

            experience = request.form.get(
                "experience",
                ""
            ).strip()

            portfolio = request.form.get(
                "portfolio",
                ""
            ).strip()

            about = request.form.get(
                "about",
                ""
            ).strip()

            if not expertise or not experience:

                flash(
                    "Please provide your professional expertise "
                    "and experience."
                )

                return redirect(
                    url_for("register")
                )

            user = User(
                name=name,
                email=email,
                password=generate_password_hash(
                    password
                ),
                role="professional"
            )

            db.session.add(user)

            db.session.flush()

            professional_profile = ProfessionalProfile(
                user_id=user.id,
                expertise=expertise,
                experience=experience,
                portfolio=portfolio,
                about=about,
                verification_status="Pending",
                profile_completed=False
            )

            db.session.add(
                professional_profile
            )

            db.session.commit()

            _issue_email_verification(user)

            flash(
                "Professional account created successfully. "
                "Please login."
            )

            return redirect(
                url_for("login")
            )

        # =================================================
        # CUSTOMER REGISTRATION
        # =================================================

        user = User(
            name=name,
            email=email,
            password=generate_password_hash(
                password
            ),
            role="customer"
        )

        db.session.add(user)

        db.session.flush()

        customer_profile = CustomerProfile(
            user_id=user.id
        )

        db.session.add(
            customer_profile
        )

        db.session.commit()

        _issue_email_verification(user)

        flash(
            "Customer account created successfully. "
            "Please login."
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "register.html"
    )


# =========================================================
# CUSTOMER / PROFESSIONAL / ADMIN LOGIN
# =========================================================

@auth_bp.route(
    "/login",
    methods=["GET", "POST"]
)
@csrf.exempt
@limiter.limit("5 per minute")
@limiter.limit("20 per hour")
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        login_role = request.form.get(
            "login_role",
            ""
        ).strip().lower()

        # -------------------------------------------------
        # VALIDATE LOGIN ROLE
        # -------------------------------------------------

        if login_role not in (
            "customer",
            "professional",
            "admin"
        ):

            flash(
                "Please select how you want to login.",
                "login_error"
            )

            return redirect(
                url_for("login")
            )

        # -------------------------------------------------
        # FIND USER BY EMAIL + ROLE
        # -------------------------------------------------

        user = User.query.filter_by(
            email=email,
            role=login_role
        ).first()

        # -------------------------------------------------
        # VERIFY PASSWORD
        # -------------------------------------------------

        if user and check_password_hash(
            user.password,
            password
        ):

            if (
                current_app.config.get(
                    "EMAIL_VERIFICATION_REQUIRED", False
                )
                and getattr(user, "email_verified_at", None) is None
            ):
                flash(
                    "Please verify your email address before logging in.",
                    "login_error",
                )
                return redirect(url_for("login"))

            csrf_token = session.get("csrf_token")
            session.clear()
            if csrf_token is not None:
                session["csrf_token"] = csrf_token
            login_user(user)
            session.permanent = True
            session["session_version"] = getattr(
                user, "session_version", 0
            )

            # ---------------------------------------------
            # ADMIN
            # ---------------------------------------------

            if user.role == "admin":

                return redirect(
                    url_for("admin_dashboard")
                )

            # ---------------------------------------------
            # PROFESSIONAL
            # ---------------------------------------------

            if user.role == "professional":

                return redirect(
                    url_for("professional_dashboard")
                )

            # ---------------------------------------------
            # CUSTOMER
            # ---------------------------------------------

            return redirect(
                url_for("dashboard")
            )

        flash(
            "Invalid email, password, or account type.",
            "login_error"
        )

    return render_template(
        "login.html"
    )


# =========================================================
# LOGOUT
# =========================================================

@auth_bp.route("/logout", methods=["GET", "POST"])
@login_required
def logout():

    if request.method == "GET":
        return render_template(
            "logout_confirm.html"
        )

    logout_user()
    session.clear()

    return redirect(
        url_for("index")
    )


# =========================================================
# CUSTOMER PROFILE
# =========================================================


# =========================================================
# PASSWORD RESET
# =========================================================

@auth_bp.route(
    "/forgot-password",
    methods=["GET", "POST"]
)
@limiter.limit("5 per hour")
def forgot_password():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()

        users = User.query.filter_by(email=email).all()

        for user in users:

            expires_at = get_ist_now() + timedelta(
                minutes=current_app.config.get(
                "PASSWORD_RESET_TOKEN_EXPIRY_MINUTES", 30
            )
            )
            raw_token = _create_user_token(
                user, "password_reset", expires_at
            )
            reset_link = _trusted_external_url(
                "reset_password", token=raw_token
            )

            try:

                send_email(
                    user.email,
                    "Reset your AgencyOS password",
                    "Reset your password:\n\n%s" % reset_link,
                )

            except EmailDeliveryError:

                logger.error(
                    "Password reset delivery failed for user %s",
                    user.id,
                )

        flash(
            "If an account with that email exists, "
            "a password reset link has been sent."
        )

        return redirect(url_for("login"))

    return render_template("forgot_password.html")


@auth_bp.route(
    "/reset-password/<token>",
    methods=["GET", "POST"]
)
@limiter.limit("10 per hour")
def reset_password(token):

    user_token = _get_valid_token(token, "password_reset")

    if user_token is None:

        flash("This password reset link is invalid or expired.")
        return redirect(url_for("forgot_password"))

    user = User.query.get(user_token.user_id)

    if user is None:

        flash("This password reset link is invalid or expired.")
        return redirect(url_for("forgot_password"))

    if request.method == "POST":

        password = request.form.get("password", "")
        confirm_password = request.form.get(
            "confirm_password", ""
        )

        if not _validate_password_policy(password) or password != confirm_password:

            flash("Passwords do not match or fail password policy.")

            return redirect(
                url_for("reset_password", token=token)
            )

        consumed = (
            UserToken.query
            .filter_by(id=user_token.id, used_at=None)
            .update(
                {"used_at": get_ist_now()},
                synchronize_session=False,
            )
        )

        if consumed != 1:
            db.session.rollback()
            flash("This password reset link is invalid or expired.")
            return redirect(url_for("forgot_password"))

        user.password = generate_password_hash(password)
        user.session_version = (
            (user.session_version or 0) + 1
        )

        # Invalidate any other outstanding reset tokens for this user.
        UserToken.query.filter_by(
            user_id=user.id,
            purpose="password_reset",
            used_at=None,
        ).update(
            {"used_at": get_ist_now()},
            synchronize_session=False,
        )

        db.session.commit()

        flash("Your password has been reset. Please log in.")
        return redirect(url_for("login"))

    return render_template(
        "reset_password.html", token=token
    )


# =========================================================
# EMAIL VERIFICATION
# =========================================================

@auth_bp.route("/verify-email/<token>")
def verify_email(token):

    user_token = _get_valid_token(token, "email_verification")

    if user_token is None:

        flash("This verification link is invalid or expired.")
        return redirect(url_for("login"))

    user = User.query.get(user_token.user_id)

    if user is None:

        flash("This verification link is invalid or expired.")
        return redirect(url_for("login"))

    consumed = (
        UserToken.query
        .filter_by(id=user_token.id, used_at=None)
        .update(
            {"used_at": get_ist_now()},
            synchronize_session=False,
        )
    )

    if consumed != 1:
        db.session.rollback()
        flash("This verification link is invalid or expired.")
        return redirect(url_for("login"))

    user.email_verified_at = get_ist_now()
    db.session.commit()

    flash("Your email address has been verified.")
    return redirect(url_for("login"))


@auth_bp.route(
    "/resend-verification",
    methods=["POST"]
)
@limiter.limit("5 per hour")
def resend_verification():

    email = request.form.get("email", "").strip().lower()

    users = User.query.filter_by(email=email).all()

    for user in users:

        if user.email_verified_at is None:

            expires_at = get_ist_now() + timedelta(
                hours=current_app.config.get(
                    "EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS", 24
                )
            )
            raw_token = _create_user_token(
                user, "email_verification", expires_at
            )
            verification_link = _trusted_external_url(
                "verify_email", token=raw_token
            )

            try:

                send_email(
                    user.email,
                    "Verify your AgencyOS email address",
                    "Verify your email address:\n\n%s"
                    % verification_link,
                )

            except EmailDeliveryError:

                logger.error(
                    "Email verification delivery failed for user %s",
                    user.id,
                )

    flash(
        "If an account with that email exists, "
        "a verification link has been sent."
    )

    return redirect(url_for("login"))
