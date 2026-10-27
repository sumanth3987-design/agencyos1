from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, csrf
from app.models import User, CustomerProfile, ProfessionalProfile

auth_bp = Blueprint("auth", __name__)

# CSRF tokens are required for state-changing requests on authenticated
# sessions (e.g. POST /logout). Login and registration endpoints are
# excluded because they are the initial authentication steps used by
# anonymous visitors before a session exists.

@auth_bp.route("/")
def index():

    return render_template(
        "index.html"
    )


# =========================================================
# CUSTOMER / PROFESSIONAL REGISTER
# =========================================================

@auth_bp.route(
    "/register",
    methods=["GET", "POST"]
)
@csrf.exempt
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

            if account_type == "customer":

                flash(
                    "A Customer account with this email "
                    "already exists."
                )

            else:

                flash(
                    "A Professional account with this email "
                    "already exists."
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

            login_user(user)

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

    return redirect(
        url_for("index")
    )


# =========================================================
# CUSTOMER PROFILE
# =========================================================


