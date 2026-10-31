
import profile

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify
)

from flask_sqlalchemy import SQLAlchemy

from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from dotenv import load_dotenv

from datetime import datetime
from zoneinfo import ZoneInfo

import os
import json
from urllib.parse import urlparse

import razorpay


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()

RAZORPAY_KEY_ID = os.getenv(
    "RAZORPAY_KEY_ID"
)

RAZORPAY_KEY_SECRET = os.getenv(
    "RAZORPAY_KEY_SECRET"
)

razorpay_client = razorpay.Client(
    auth=(
        RAZORPAY_KEY_ID,
        RAZORPAY_KEY_SECRET
    )
)


# =========================================================
# APP CONFIGURATION
# =========================================================

app = Flask(
    __name__,
    template_folder="templates"
)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///agencyos.db"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

login_manager = LoginManager(app)

login_manager.login_view = "login"


# =========================================================
# TIMEZONE
# =========================================================

IST = ZoneInfo("Asia/Kolkata")


def get_ist_now():
    return datetime.now(IST)


# =========================================================
# URL VALIDATION
# =========================================================

def is_valid_http_url(value):
    """
    Validate that a supplied URL uses HTTP or HTTPS.
    """

    if not value:
        return False

    try:

        parsed = urlparse(
            value.strip()
        )

        return (
            parsed.scheme in ("http", "https")
            and bool(parsed.netloc)
        )

    except Exception:

        return False


# =========================================================
# PACKAGE PRICES
# =========================================================

PACKAGE_PRICES = {

    "Basic Website": 4999,

    "Business Website": 9999,

    "Advanced Website": 19999,

    "SEO Starter": 2999,

    "SEO Growth": 6999,

    "SEO Advanced": 12000
}


# =========================================================
# USER MODEL
# =========================================================

class User(UserMixin, db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.String(30),
        default="customer"
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    projects = db.relationship(
        "Project",
        backref="customer",
        lazy=True
    )

    professional_profile = db.relationship(
        "ProfessionalProfile",
        backref="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    customer_profile = db.relationship(
        "CustomerProfile",
        backref="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    businesses = db.relationship(
    "Business",
    back_populates="customer",
    cascade="all, delete-orphan",
    lazy=True
)


# =========================================================
# CUSTOMER PROFILE MODEL
# =========================================================

class CustomerProfile(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        unique=True,
        nullable=False
    )

    phone = db.Column(
        db.String(30),
        nullable=True
    )

    location = db.Column(
        db.String(150),
        nullable=True
    )

    business_name = db.Column(
        db.String(150),
        nullable=True
    )

    business_type = db.Column(
        db.String(100),
        nullable=True
    )

    website = db.Column(
        db.String(300),
        nullable=True
    )

    social_links = db.Column(
        db.Text,
        nullable=True
    )

    business_description = db.Column(
        db.Text,
        nullable=True
    )

    target_audience = db.Column(
        db.Text,
        nullable=True
    )

    business_goals = db.Column(
        db.Text,
        nullable=True
    )

    preferred_budget = db.Column(
        db.String(100),
        nullable=True
    )

    profile_completed = db.Column(
        db.Boolean,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now()
    )
class Business(db.Model):
    __tablename__ = "business"

    id = db.Column(db.Integer, primary_key=True)

    customer_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    name = db.Column(
        db.String(200),
        nullable=False
    )

    business_type = db.Column(
        db.String(150),
        nullable=True
    )

    location = db.Column(
        db.String(250),
        nullable=True
    )

    website = db.Column(
        db.String(500),
        nullable=True
    )

    social_links = db.Column(
        db.Text,
        nullable=True
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    target_audience = db.Column(
        db.Text,
        nullable=True
    )

    goals = db.Column(
        db.Text,
        nullable=True
    )

    preferred_budget = db.Column(
        db.String(100),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=get_ist_now
    )

    updated_at = db.Column(
        db.DateTime,
        default=get_ist_now,
        onupdate=get_ist_now
    )

    customer = db.relationship(
        "User",
        back_populates="businesses"
    )

    projects = db.relationship(
        "Project",
        back_populates="business",
        lazy=True
    )

# =========================================================
# PROFESSIONAL PROFILE MODEL
# =========================================================

class ProfessionalProfile(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        unique=True,
        nullable=False
    )

    expertise = db.Column(
        db.String(100),
        nullable=False,
        default=""
    )

    experience = db.Column(
        db.String(50),
        nullable=False,
        default=""
    )

    about = db.Column(
        db.Text,
        nullable=True
    )

    phone = db.Column(
        db.String(30),
        nullable=True
    )

    location = db.Column(
        db.String(150),
        nullable=True
    )

    skills = db.Column(
        db.Text,
        nullable=True
    )

    technologies = db.Column(
        db.Text,
        nullable=True
    )

    skill_level = db.Column(
        db.String(50),
        nullable=True
    )

    project_types = db.Column(
        db.Text,
        nullable=True
    )

    portfolio = db.Column(
        db.String(500),
        nullable=True
    )

    github = db.Column(
        db.String(300),
        nullable=True
    )

    linkedin = db.Column(
        db.String(300),
        nullable=True
    )

    education = db.Column(
        db.Text,
        nullable=True
    )

    certifications = db.Column(
        db.Text,
        nullable=True
    )

    work_experience = db.Column(
        db.Text,
        nullable=True
    )

    availability = db.Column(
        db.String(50),
        nullable=True
    )

    current_workload = db.Column(
        db.String(100),
        nullable=True
    )

    verification_status = db.Column(
        db.String(30),
        default="Pending"
    )

    verification_notes = db.Column(
        db.Text,
        nullable=True
    )

    profile_completed = db.Column(
        db.Boolean,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now()
    )


# =========================================================
# PROJECT MODEL
# =========================================================

class Project(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    customer_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    business_id = db.Column(
    db.Integer,
    db.ForeignKey("business.id"),
    nullable=True
    )

    business = db.relationship(
    "Business",
    back_populates="projects"
    )

    service = db.Column(
        db.String(100),
        nullable=False
    )

    package = db.Column(
        db.String(100),
        nullable=False
    )

    requirements = db.Column(
        db.Text,
        nullable=False
    )

    status = db.Column(
        db.String(50),
        default="Pending Assignment"
    )

    revision_comment = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        nullable=False
    )


# =========================================================
# PAYMENT MODEL
# =========================================================

class Payment(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    project_id = db.Column(
        db.Integer,
        db.ForeignKey("project.id"),
        nullable=False
    )

    customer_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    razorpay_order_id = db.Column(
        db.String(100),
        nullable=False
    )

    razorpay_payment_id = db.Column(
        db.String(100),
        nullable=True
    )

    amount = db.Column(
        db.Integer,
        nullable=False
    )

    currency = db.Column(
        db.String(10),
        default="INR",
        nullable=False
    )

    status = db.Column(
        db.String(30),
        default="Created",
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        nullable=False
    )

    paid_at = db.Column(
        db.DateTime,
        nullable=True
    )

    project = db.relationship(
        "Project",
        backref="payments"
    )

    customer = db.relationship(
        "User",
        backref="payments"
    )


# =========================================================
# PROFESSIONAL PROJECT APPLICATION
# =========================================================

class ProfessionalProjectApplication(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    project_id = db.Column(
        db.Integer,
        db.ForeignKey("project.id"),
        nullable=False
    )

    professional_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    status = db.Column(
        db.String(30),
        default="Applied"
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    project = db.relationship(
        "Project",
        backref="applications"
    )

    professional = db.relationship(
        "User",
        backref="project_applications"
    )


# =========================================================
# PROJECT DELIVERY MODEL
# =========================================================

class ProjectDelivery(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    project_id = db.Column(
        db.Integer,
        db.ForeignKey("project.id"),
        nullable=False,
        index=True
    )

    professional_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False,
        index=True
    )

    submission_number = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )

    live_url = db.Column(
        db.String(500),
        nullable=True
    )

    source_url = db.Column(
        db.String(500),
        nullable=True
    )

    preview_url = db.Column(
        db.String(500),
        nullable=True
    )

    completion_notes = db.Column(
        db.Text,
        nullable=False
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="Submitted"
    )

    review_comment = db.Column(
        db.Text,
        nullable=True
    )

    submitted_at = db.Column(
        db.DateTime,
        nullable=False,
        default=get_ist_now
    )

    reviewed_at = db.Column(
        db.DateTime,
        nullable=True
    )

    project = db.relationship(
        "Project",
        backref=db.backref(
            "deliveries",
            lazy=True,
            order_by="ProjectDelivery.submission_number"
        )
    )

    professional = db.relationship(
        "User",
        backref="project_deliveries"
    )


# =========================================================
# SERVICES
# =========================================================

services = [

    {
        "slug": "website-development",
        "name": "Website Design & Development",
        "description":
            "Professional websites for businesses, "
            "portfolios, startups and organizations.",
        "icon": "🌐",
        "packages": [
            {
                "id": "website-basic",
                "name": "Basic Website",
                "price": 4999
            },
            {
                "id": "website-business",
                "name": "Business Website",
                "price": 9999
            },
            {
                "id": "website-advanced",
                "name": "Advanced Website",
                "price": 19999
            }
        ]
    },

    {
        "slug": "seo",
        "name": "SEO",
        "description":
            "Search engine optimization to improve "
            "website visibility and organic traffic.",
        "icon": "📈",
        "packages": [
            {
                "id": "seo-starter",
                "name": "SEO Starter",
                "price": 2999
            },
            {
                "id": "seo-growth",
                "name": "SEO Growth",
                "price": 6999
            },
            {
                "id": "seo-advanced",
                "name": "SEO Advanced",
                "price": 12000
            }
        ]
    }
]
# ========================================================
# Professional expertise matching helper
# =========================================================

def professional_has_expertise(profile, service):

    if not profile or not profile.expertise or not service:
        return False

    expertise_values = [
        item.strip()
        for item in profile.expertise.split(",")
        if item.strip()
    ]

    return service.strip() in expertise_values

# =========================================================
# PROFILE COMPLETION HELPERS
# =========================================================

def calculate_professional_profile_completion(profile):

    if not profile:
        return 0

    fields = [
        profile.expertise,
        profile.experience,
        profile.about,
        profile.phone,
        profile.location,
        profile.skills,
        profile.technologies,
        profile.skill_level,
        profile.project_types,
        profile.portfolio,
        profile.github,
        profile.linkedin,
        profile.education,
        profile.certifications,
        profile.work_experience,
        profile.availability,
        profile.current_workload
    ]

    completed = sum(
        1
        for field in fields
        if field and str(field).strip()
    )

    total = len(fields)

    if total == 0:
        return 0

    return round(
        (completed / total) * 100
    )


def calculate_customer_profile_completion(profile):

    if not profile:
        return 0

    fields = [
        profile.phone,
        profile.location,
        profile.business_name,
        profile.business_type,
        profile.website,
        profile.social_links,
        profile.business_description,
        profile.target_audience,
        profile.business_goals,
        profile.preferred_budget
    ]

    completed = sum(
        1
        for field in fields
        if field and str(field).strip()
    )

    total = len(fields)

    if total == 0:
        return 0

    return round(
        (completed / total) * 100
    )

def get_business_for_customer(business_id, customer_id):

    if not business_id:
        return None

    try:
        business_id = int(business_id)
    except (TypeError, ValueError):
        return None

    return (
        Business.query
        .filter_by(
            id=business_id,
            customer_id=customer_id
        )
        .first()
    )

# =========================================================
# GET ASSIGNED PROFESSIONAL APPLICATION
# =========================================================

def get_assigned_professional_application(project_id):

    return ProfessionalProjectApplication.query.filter_by(
        project_id=project_id,
        professional_id=current_user.id,
        status="Assigned"
    ).first()


# =========================================================
# GET LATEST DELIVERY
# =========================================================

def get_latest_project_delivery(project_id):

    return (
        ProjectDelivery.query
        .filter_by(
            project_id=project_id
        )
        .order_by(
            ProjectDelivery.submission_number.desc()
        )
        .first()
    )


# =========================================================
# LOGIN LOADER
# =========================================================

@login_manager.user_loader
def load_user(user_id):

    return User.query.get(
        int(user_id)
    )


# =========================================================
# HOME
# =========================================================

@app.route("/")
def index():

    return render_template(
        "index.html"
    )


# =========================================================
# CUSTOMER / PROFESSIONAL REGISTER
# =========================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
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

@app.route(
    "/login",
    methods=["GET", "POST"]
)
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

@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(
        url_for("index")
    )


# =========================================================
# CUSTOMER PROFILE
# =========================================================

@app.route(
    "/customer/profile",
    methods=["GET", "POST"]
)
@login_required
def customer_profile():

    if current_user.role != "customer":

        return redirect(
            url_for("dashboard")
        )

    profile = CustomerProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    if not profile:

        profile = CustomerProfile(
            user_id=current_user.id
        )

        db.session.add(profile)

        db.session.commit()

    if request.method == "POST":

        profile.phone = request.form.get(
            "phone",
            ""
        ).strip()

        profile.location = request.form.get(
            "location",
            ""
        ).strip()

        profile.business_name = request.form.get(
            "business_name",
            ""
        ).strip()

        profile.business_type = request.form.get(
            "business_type",
            ""
        ).strip()

        profile.website = request.form.get(
            "website",
            ""
        ).strip()

        profile.social_links = request.form.get(
            "social_links",
            ""
        ).strip()

        profile.business_description = request.form.get(
            "business_description",
            ""
        ).strip()

        profile.target_audience = request.form.get(
            "target_audience",
            ""
        ).strip()

        profile.business_goals = request.form.get(
            "business_goals",
            ""
        ).strip()

        profile.preferred_budget = request.form.get(
            "preferred_budget",
            ""
        ).strip()

        required_profile_fields = [
            profile.phone,
            profile.location,
            profile.business_name,
            profile.business_type,
            profile.business_description,
            profile.target_audience,
            profile.business_goals
        ]

        profile.profile_completed = all(
            field
            for field in required_profile_fields
        )

        db.session.commit()

        flash(
            "Customer profile saved successfully."
        )

        return redirect(
            url_for("customer_profile")
        )

    return render_template(
        "customer_profile.html",
        customer_profile=profile
    )


# =========================================================
# CUSTOMER DASHBOARD
# =========================================================

@app.route("/dashboard")
@login_required
def dashboard():

    if current_user.role == "admin":

        return redirect(
            url_for("admin_dashboard")
        )

    if current_user.role == "professional":

        return redirect(
            url_for("professional_dashboard")
        )

    projects = Project.query.filter_by(
        customer_id=current_user.id
    ).order_by(
        Project.created_at.desc()
    ).all()

    customer_profile = CustomerProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    profile_completion = 0

    if customer_profile:

        profile_fields = [
            customer_profile.phone,
            customer_profile.location,
            customer_profile.business_name,
            customer_profile.business_type,
            customer_profile.website,
            customer_profile.social_links,
            customer_profile.business_description,
            customer_profile.target_audience,
            customer_profile.business_goals,
            customer_profile.preferred_budget
        ]

        completed_fields = sum(
            1
            for field in profile_fields
            if field and str(field).strip()
        )

        total_fields = len(
            profile_fields
        )

        if total_fields > 0:

            profile_completion = round(
                (
                    completed_fields
                    / total_fields
                ) * 100
            )

    return render_template(
        "dashboard.html",
        projects=projects,
        services=services,
        customer_profile=customer_profile,
        profile_completion=profile_completion
    )


# =========================================================
# CUSTOMER PROJECT DETAILS
# =========================================================

@app.route(
    "/project/<int:project_id>"
)
@login_required
def project_details(project_id):

    if current_user.role != "customer":

        flash(
            "Access denied."
        )

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

    assigned_application = (
        ProfessionalProjectApplication.query
        .filter_by(
            project_id=project.id,
            status="Assigned"
        )
        .first()
    )

    assigned_professional = None

    professional_profile = None

    if assigned_application:

        assigned_professional = (
            assigned_application.professional
        )

        if assigned_professional:

            professional_profile = (
                ProfessionalProfile.query
                .filter_by(
                    user_id=assigned_professional.id
                )
                .first()
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

    delivery_history = (
        ProjectDelivery.query
        .filter_by(
            project_id=project.id
        )
        .order_by(
            ProjectDelivery.submission_number.asc()
        )
        .all()
    )

    latest_delivery = get_latest_project_delivery(
        project.id
    )

    project_steps = [
        {
            "name": "Project Created",
            "description":
                "Your project has been submitted to AgencyOS.",
            "statuses": [
                "Payment Pending",
                "Pending Assignment",
                "Assigned",
                "In Progress",
                "Submitted",
                "Revision",
                "Completed"
            ]
        },
        {
            "name": "Professional Assignment",
            "description":
                "A suitable professional is assigned to your project.",
            "statuses": [
                "Assigned",
                "In Progress",
                "Submitted",
                "Revision",
                "Completed"
            ]
        },
        {
            "name": "Work in Progress",
            "description":
                "The assigned professional is working on your project.",
            "statuses": [
                "In Progress",
                "Submitted",
                "Revision",
                "Completed"
            ]
        },
        {
            "name": "Agency Review",
            "description":
                "The completed work is being reviewed by AgencyOS.",
            "statuses": [
                "Submitted",
                "Revision",
                "Completed"
            ]
        },
        {
            "name": "Project Completed",
            "description":
                "Your project has been approved and completed.",
            "statuses": [
                "Completed"
            ]
        }
    ]

    status_order = [
        "Payment Pending",
        "Pending Assignment",
        "Assigned",
        "In Progress",
        "Submitted",
        "Revision",
        "Completed"
    ]

    current_status_index = 0

    if project.status in status_order:

        current_status_index = (
            status_order.index(
                project.status
            )
        )

    return render_template(
        "project_details.html",
        project=project,
        amount=amount,
        payment=payment,
        assigned_professional=assigned_professional,
        professional_profile=professional_profile,
        project_steps=project_steps,
        current_status_index=current_status_index,
        latest_delivery=latest_delivery,
        delivery_history=delivery_history
    )


# =========================================================
# PROFESSIONAL PROFILE
# =========================================================

@app.route(
    "/professional/profile",
    methods=["GET", "POST"]
)
@login_required
def professional_profile():

    if current_user.role != "professional":

        return redirect(
            url_for("dashboard")
        )

    profile = ProfessionalProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    if not profile:

        profile = ProfessionalProfile(
            user_id=current_user.id
        )

        db.session.add(profile)

        db.session.commit()

    if request.method == "POST":

        # -------------------------------------------------
        # MULTIPLE PROFESSIONAL EXPERTISE
        # -------------------------------------------------

        expertise_values = request.form.getlist(
            "expertise"
        )

        profile.expertise = ", ".join(
            item.strip()
            for item in expertise_values
            if item.strip()
        )

        # -------------------------------------------------
        # BASIC INFORMATION
        # -------------------------------------------------

        profile.experience = request.form.get(
            "experience",
            ""
        ).strip()

        profile.about = request.form.get(
            "about",
            ""
        ).strip()

        profile.phone = request.form.get(
            "phone",
            ""
        ).strip()

        profile.location = request.form.get(
            "location",
            ""
        ).strip()

        # -------------------------------------------------
        # MULTIPLE SKILLS
        # -------------------------------------------------

        selected_skills = request.form.getlist(
            "skills"
        )

        profile.skills = json.dumps(
            selected_skills
        )

        # -------------------------------------------------
        # OTHER PROFESSIONAL INFORMATION
        # -------------------------------------------------

        profile.technologies = request.form.get(
            "technologies",
            ""
        ).strip()

        profile.skill_level = request.form.get(
            "skill_level",
            ""
        ).strip()

        profile.project_types = request.form.get(
            "project_types",
            ""
        ).strip()

        profile.portfolio = request.form.get(
            "portfolio",
            ""
        ).strip()

        profile.github = request.form.get(
            "github",
            ""
        ).strip()

        profile.linkedin = request.form.get(
            "linkedin",
            ""
        ).strip()

        profile.education = request.form.get(
            "education",
            ""
        ).strip()

        profile.certifications = request.form.get(
            "certifications",
            ""
        ).strip()

        profile.work_experience = request.form.get(
            "work_experience",
            ""
        ).strip()

        profile.availability = request.form.get(
            "availability",
            ""
        ).strip()

        profile.current_workload = request.form.get(
            "current_workload",
            ""
        ).strip()

        # -------------------------------------------------
        # PROFILE COMPLETION
        # -------------------------------------------------

        profile_completion = (
            calculate_professional_profile_completion(
                profile
            )
        )

        profile.profile_completed = (
            profile_completion == 100
        )

        db.session.commit()

        flash(
            "Professional profile saved successfully."
        )

        return redirect(
            url_for("professional_profile")
        )

    # =====================================================
    # LOAD SELECTED EXPERTISE
    # =====================================================

    selected_expertise = []

    if profile.expertise:

        selected_expertise = [
            item.strip()
            for item in profile.expertise.split(",")
            if item.strip()
        ]

    # =====================================================
    # LOAD SELECTED SKILLS
    # =====================================================

    selected_skills = []

    if profile.skills:

        try:

            selected_skills = json.loads(
                profile.skills
            )

            if not isinstance(
                selected_skills,
                list
            ):

                selected_skills = []

        except (
            json.JSONDecodeError,
            TypeError
        ):

            # Support old single-skill value
            if profile.skills.strip():

                selected_skills = [
                    profile.skills.strip()
                ]

    # =====================================================
    # PROFILE COMPLETION
    # =====================================================

    profile_completion = (
        calculate_professional_profile_completion(
            profile
        )
    )

    return render_template(
        "professional_profile.html",
        profile=profile,
        profile_completion=profile_completion,
        selected_expertise=selected_expertise,
        selected_skills=selected_skills
    )

# =========================================================
# PROFESSIONAL DASHBOARD
# =========================================================

@app.route(
    "/professional/dashboard"
)
@login_required
def professional_dashboard():

    if current_user.role != "professional":

        return redirect(
            url_for("dashboard")
        )

    profile = ProfessionalProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    assigned_projects = (
        Project.query
        .join(
            ProfessionalProjectApplication,
            ProfessionalProjectApplication.project_id
            == Project.id
        )
        .filter(
            ProfessionalProjectApplication.professional_id
            == current_user.id,
            ProfessionalProjectApplication.status
            == "Assigned"
        )
        .order_by(
            Project.created_at.desc()
        )
        .all()
    )

    available_projects = []

    if (
        profile
        and profile.verification_status == "Verified"
    ):

        # Find all pending projects matching any of the professional's expertise
        available_projects = [
            project
            for project in Project.query.filter(
                Project.status == "Pending Assignment"
            ).order_by(
                Project.created_at.desc()
            ).all()
            if professional_has_expertise(profile, project.service)
        ]

    total_projects = len(
        assigned_projects
    )

    completed_projects = sum(
        1
        for project in assigned_projects
        if project.status == "Completed"
    )

    in_progress_projects = sum(
        1
        for project in assigned_projects
        if project.status == "In Progress"
    )

    submitted_projects = sum(
        1
        for project in assigned_projects
        if project.status == "Submitted"
    )

    revision_projects = sum(
        1
        for project in assigned_projects
        if project.status == "Revision"
    )

    profile_completion = (
        calculate_professional_profile_completion(
            profile
        )
        if profile
        else 0
    )

    return render_template(
        "professional_dashboard.html",
        profile=profile,
        assigned_projects=assigned_projects,
        available_projects=available_projects,
        projects=assigned_projects,
        total_projects=total_projects,
        completed_projects=completed_projects,
        in_progress_projects=in_progress_projects,
        submitted_projects=submitted_projects,
        revision_projects=revision_projects,
        profile_completion=profile_completion
    )


# =========================================================
# PROFESSIONAL AVAILABLE PROJECTS
# =========================================================

@app.route(
    "/professional/projects"
)
@login_required
def professional_projects():

    if current_user.role != "professional":

        return redirect(
            url_for("dashboard")
        )

    profile = ProfessionalProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    if not profile:

        flash(
            "Professional profile not found."
        )

        return redirect(
            url_for("professional_dashboard")
        )

    if profile.verification_status != "Verified":

        flash(
            "Your professional account must be verified "
            "before viewing available projects."
        )

        return redirect(
            url_for("professional_dashboard")
        )

    # Find all pending projects matching any of the professional's expertise
    projects = [
        project
        for project in Project.query.filter(
            Project.status == "Pending Assignment"
        ).order_by(
            Project.created_at.desc()
        ).all()
        if professional_has_expertise(profile, project.service)
    ]

    return render_template(
        "professional_projects.html",
        projects=projects
    )

# =========================================================
# APPLY FOR PROJECT
# =========================================================

@app.route(
    "/professional/projects/<int:project_id>/apply",
    methods=["POST"]
)
@login_required
def apply_project(project_id):

    if current_user.role != "professional":

        flash(
            "Only professionals can apply for projects."
        )

        return redirect(
            url_for("dashboard")
        )

    profile = ProfessionalProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    if not profile:

        flash(
            "Professional profile not found."
        )

        return redirect(
            url_for("professional_dashboard")
        )

    if profile.verification_status != "Verified":

        flash(
            "Your account must be verified before applying."
        )

        return redirect(
            url_for("professional_dashboard")
        )

    project = Project.query.get_or_404(
        project_id
    )

    if project.status != "Pending Assignment":

        flash(
            "This project is no longer available."
        )

        return redirect(
            url_for("professional_projects")
        )

    # Check whether the project matches any of the professional's expertise
    if not professional_has_expertise(
        profile,
        project.service
    ):

        flash(
            "This project does not match your expertise."
        )

        return redirect(
            url_for("professional_projects")
        )

    existing_application = (
        ProfessionalProjectApplication.query.filter_by(
            project_id=project.id,
            professional_id=current_user.id
        ).first()
    )

    if existing_application:

        flash(
            "You have already applied for this project."
        )

        return redirect(
            url_for("professional_projects")
        )

    application = ProfessionalProjectApplication(
        project_id=project.id,
        professional_id=current_user.id,
        status="Applied"
    )

    db.session.add(
        application
    )

    db.session.commit()

    flash(
        "Project application submitted successfully."
    )

    return redirect(
        url_for("professional_projects")
    )

# =========================================================
# START PROFESSIONAL PROJECT
# =========================================================

@app.route(
    "/professional/project/<int:project_id>/start",
    methods=["POST"]
)
@login_required
def start_professional_project(project_id):

    if current_user.role != "professional":

        flash(
            "Only professionals can start projects."
        )

        return redirect(
            url_for("dashboard")
        )

    project = Project.query.get_or_404(
        project_id
    )

    application = get_assigned_professional_application(
        project.id
    )

    if not application:

        flash(
            "You are not assigned to this project."
        )

        return redirect(
            url_for("professional_dashboard")
        )

    if project.status != "Assigned":

        flash(
            "This project cannot be started from its current status."
        )

        return redirect(
            url_for(
                "professional_project_workspace",
                project_id=project.id
            )
        )

    project.status = "In Progress"

    db.session.commit()

    flash(
        "Project started successfully."
    )

    return redirect(
        url_for(
            "professional_project_workspace",
            project_id=project.id
        )
    )


# =========================================================
# PROFESSIONAL PROJECT WORKSPACE
# =========================================================

@app.route(
    "/professional/project/<int:project_id>"
)
@login_required
def professional_project_workspace(project_id):

    if current_user.role != "professional":

        return redirect(
            url_for("dashboard")
        )

    project = Project.query.get_or_404(
        project_id
    )

    application = get_assigned_professional_application(
        project.id
    )

    if not application:

        flash(
            "You are not assigned to this project."
        )

        return redirect(
            url_for("professional_dashboard")
        )

    latest_delivery = get_latest_project_delivery(
        project.id
    )

    delivery_history = (
        ProjectDelivery.query
        .filter_by(
            project_id=project.id
        )
        .order_by(
            ProjectDelivery.submission_number.desc()
        )
        .all()
    )

    return render_template(
        "professional_project_workspace.html",
        project=project,
        latest_delivery=latest_delivery,
        delivery_history=delivery_history
    )


# =========================================================
# SUBMIT PROFESSIONAL WORK
# =========================================================

@app.route(
    "/professional/project/<int:project_id>/submit",
    methods=["POST"]
)
@login_required
def submit_professional_work(project_id):

    if current_user.role != "professional":

        flash(
            "Only professionals can submit work."
        )

        return redirect(
            url_for("dashboard")
        )

    project = Project.query.get_or_404(
        project_id
    )

    application = get_assigned_professional_application(
        project.id
    )

    if not application:

        flash(
            "You are not assigned to this project."
        )

        return redirect(
            url_for("professional_dashboard")
        )

    if project.status != "In Progress":

        flash(
            "This project is not ready for submission."
        )

        return redirect(
            url_for(
                "professional_project_workspace",
                project_id=project.id
            )
        )

    completion_notes = request.form.get(
        "completion_notes",
        ""
    ).strip()

    live_url = request.form.get(
        "live_url",
        ""
    ).strip()

    source_url = request.form.get(
        "source_url",
        ""
    ).strip()

    preview_url = request.form.get(
        "preview_url",
        ""
    ).strip()

    if not completion_notes:

        flash(
            "Please provide completion notes."
        )

        return redirect(
            url_for(
                "professional_project_workspace",
                project_id=project.id
            )
        )

    # -----------------------------------------------------
    # WEBSITE PROJECTS REQUIRE LIVE URL
    # -----------------------------------------------------

    if (
        project.service
        == "Website Design & Development"
        and not live_url
    ):

        flash(
            "A live website URL is required for website projects."
        )

        return redirect(
            url_for(
                "professional_project_workspace",
                project_id=project.id
            )
        )

    # -----------------------------------------------------
    # VALIDATE URLs
    # -----------------------------------------------------

    for label, value in [
        ("Live URL", live_url),
        ("Source URL", source_url),
        ("Preview URL", preview_url)
    ]:

        if value and not is_valid_http_url(value):

            flash(
                f"{label} must be a valid HTTP or HTTPS URL."
            )

            return redirect(
                url_for(
                    "professional_project_workspace",
                    project_id=project.id
                )
            )

    latest_delivery = get_latest_project_delivery(
        project.id
    )

    submission_number = 1

    if latest_delivery:

        submission_number = (
            latest_delivery.submission_number + 1
        )

    delivery = ProjectDelivery(
        project_id=project.id,
        professional_id=current_user.id,
        submission_number=submission_number,
        live_url=live_url or None,
        source_url=source_url or None,
        preview_url=preview_url or None,
        completion_notes=completion_notes,
        status="Submitted",
        submitted_at=get_ist_now()
    )

    db.session.add(
        delivery
    )

    project.status = "Submitted"

    project.revision_comment = None

    db.session.commit()

    flash(
        "Work submitted successfully for review."
    )

    return redirect(
        url_for(
            "professional_project_workspace",
            project_id=project.id
        )
    )


# =========================================================
# RESUBMIT AFTER REVISION
# =========================================================

@app.route(
    "/professional/project/<int:project_id>/resubmit",
    methods=["POST"]
)
@login_required
def resubmit_professional_work(project_id):

    if current_user.role != "professional":

        flash(
            "Only professionals can resubmit work."
        )

        return redirect(
            url_for("dashboard")
        )

    project = Project.query.get_or_404(
        project_id
    )

    application = get_assigned_professional_application(
        project.id
    )

    if not application:

        flash(
            "You are not assigned to this project."
        )

        return redirect(
            url_for("professional_dashboard")
        )

    if project.status != "Revision":

        flash(
            "This project is not currently requesting a revision."
        )

        return redirect(
            url_for(
                "professional_project_workspace",
                project_id=project.id
            )
        )

    completion_notes = request.form.get(
        "completion_notes",
        ""
    ).strip()

    live_url = request.form.get(
        "live_url",
        ""
    ).strip()

    source_url = request.form.get(
        "source_url",
        ""
    ).strip()

    preview_url = request.form.get(
        "preview_url",
        ""
    ).strip()

    if not completion_notes:

        flash(
            "Please provide completion notes."
        )

        return redirect(
            url_for(
                "professional_project_workspace",
                project_id=project.id
            )
        )

    if (
        project.service
        == "Website Design & Development"
        and not live_url
    ):

        flash(
            "A live website URL is required for website projects."
        )

        return redirect(
            url_for(
                "professional_project_workspace",
                project_id=project.id
            )
        )

    for label, value in [
        ("Live URL", live_url),
        ("Source URL", source_url),
        ("Preview URL", preview_url)
    ]:

        if value and not is_valid_http_url(value):

            flash(
                f"{label} must be a valid HTTP or HTTPS URL."
            )

            return redirect(
                url_for(
                    "professional_project_workspace",
                    project_id=project.id
                )
            )

    latest_delivery = get_latest_project_delivery(
        project.id
    )

    # -----------------------------------------------------
    # STORE REVISION REQUEST ON PREVIOUS DELIVERY
    # -----------------------------------------------------

    if latest_delivery:

        latest_delivery.status = "Revision"

        # IMPORTANT:
        # ProjectDelivery uses review_comment.
        latest_delivery.review_comment = (
            project.revision_comment
        )

    submission_number = 1

    if latest_delivery:

        submission_number = (
            latest_delivery.submission_number + 1
        )

    delivery = ProjectDelivery(
        project_id=project.id,
        professional_id=current_user.id,
        submission_number=submission_number,
        live_url=live_url or None,
        source_url=source_url or None,
        preview_url=preview_url or None,
        completion_notes=completion_notes,
        status="Submitted",
        submitted_at=get_ist_now()
    )

    db.session.add(
        delivery
    )

    project.status = "Submitted"

    project.revision_comment = None

    db.session.commit()

    flash(
        "Revised work submitted successfully for review."
    )

    return redirect(
        url_for(
            "professional_project_workspace",
            project_id=project.id
        )
    )


# =========================================================
# PROFESSIONAL MY PROJECTS
# =========================================================

@app.route(
    "/professional/my-projects"
)
@login_required
def professional_my_projects():

    if current_user.role != "professional":

        return redirect(
            url_for("dashboard")
        )

    projects = (
        Project.query
        .join(
            ProfessionalProjectApplication,
            ProfessionalProjectApplication.project_id
            == Project.id
        )
        .filter(
            ProfessionalProjectApplication.professional_id
            == current_user.id,
            ProfessionalProjectApplication.status
            == "Assigned"
        )
        .order_by(
            Project.created_at.desc()
        )
        .all()
    )

    return render_template(
        "professional_my_projects.html",
        projects=projects
    )
# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin/dashboard")
@login_required
def admin_dashboard():

    if current_user.role != "admin":
        flash("Admin access required.")
        return redirect(url_for("dashboard"))

    customer_count = User.query.filter_by(
        role="customer"
    ).count()

    professional_count = User.query.filter_by(
        role="professional"
    ).count()

    project_count = Project.query.count()

    pending_project_count = Project.query.filter_by(
        status="Pending Assignment"
    ).count()

    pending_verification_count = ProfessionalProfile.query.filter_by(
        verification_status="Pending"
    ).count()

    application_count = ProfessionalProjectApplication.query.count()

    submitted_project_count = Project.query.filter_by(
        status="Submitted"
    ).count()

    in_progress_project_count = Project.query.filter_by(
        status="In Progress"
    ).count()

    completed_project_count = Project.query.filter_by(
        status="Completed"
    ).count()

    payment_pending_project_count = Project.query.filter_by(
        status="Payment Pending"
    ).count()

    assigned_project_count = Project.query.filter_by(
        status="Assigned"
    ).count()

    revision_project_count = Project.query.filter_by(
        status="Revision"
    ).count()

    recent_projects = (
        Project.query
        .order_by(Project.created_at.desc())
        .limit(10)
        .all()
    )

    return render_template(
        "admin_dashboard.html",
        customer_count=customer_count,
        professional_count=professional_count,
        project_count=project_count,
        pending_project_count=pending_project_count,
        pending_verification_count=pending_verification_count,
        application_count=application_count,
        submitted_project_count=submitted_project_count,
        in_progress_project_count=in_progress_project_count,
        completed_project_count=completed_project_count,
        payment_pending_project_count=payment_pending_project_count,
        assigned_project_count=assigned_project_count,
        revision_project_count=revision_project_count,
        recent_projects=recent_projects
    )

# =========================================================
# ADMIN CUSTOMERS - DEEP CUSTOMER INTELLIGENCE
# =========================================================

@app.route(
    "/admin/customers"
)
@login_required
def admin_customers():

    if current_user.role != "admin":

        flash(
            "Admin access required."
        )

        return redirect(
            url_for("dashboard")
        )

    # -----------------------------------------------------
    # GET ALL CUSTOMERS
    # -----------------------------------------------------

    customers = (
        User.query
        .filter_by(
            role="customer"
        )
        .order_by(
            User.created_at.desc()
        )
        .all()
    )

    # -----------------------------------------------------
    # CUSTOMER PROFILES
    # -----------------------------------------------------

    customer_profiles = {}

    for customer in customers:

        profile = (
            CustomerProfile.query
            .filter_by(
                user_id=customer.id
            )
            .first()
        )

        customer_profiles[
            customer.id
        ] = profile

    # -----------------------------------------------------
    # GET ALL PROJECTS
    # -----------------------------------------------------

    all_projects = (
        Project.query
        .order_by(
            Project.created_at.desc()
        )
        .all()
    )

    # -----------------------------------------------------
    # PROJECTS BY CUSTOMER
    # -----------------------------------------------------

    customer_projects = {}

    for customer in customers:

        customer_projects[
            customer.id
        ] = []

    for project in all_projects:

        if project.customer_id in customer_projects:

            customer_projects[
                project.customer_id
            ].append(project)

    # -----------------------------------------------------
    # PAYMENT INFORMATION
    #
    # Keep the latest payment record for each project.
    # This prevents multiple payment attempts from being
    # counted repeatedly in customer totals.
    # -----------------------------------------------------

    all_payments = (
        Payment.query
        .order_by(
            Payment.created_at.desc()
        )
        .all()
    )

    latest_payment_by_project = {}

    for payment in all_payments:

        if payment.project_id not in latest_payment_by_project:

            latest_payment_by_project[
                payment.project_id
            ] = payment

    # -----------------------------------------------------
    # ASSIGNED PROFESSIONALS
    # -----------------------------------------------------

    assigned_applications = (
        ProfessionalProjectApplication.query
        .filter_by(
            status="Assigned"
        )
        .all()
    )

    assigned_professional_by_project = {}

    for application in assigned_applications:

        assigned_professional_by_project[
            application.project_id
        ] = application.professional

    # -----------------------------------------------------
    # PROFESSIONAL PROFILES
    # -----------------------------------------------------

    professional_profiles = {}

    professional_users = (
        User.query
        .filter_by(
            role="professional"
        )
        .all()
    )

    for professional in professional_users:

        profile = (
            ProfessionalProfile.query
            .filter_by(
                user_id=professional.id
            )
            .first()
        )

        professional_profiles[
            professional.id
        ] = profile

    # -----------------------------------------------------
    # PROJECT DELIVERIES
    # -----------------------------------------------------

    all_deliveries = (
        ProjectDelivery.query
        .order_by(
            ProjectDelivery.submitted_at.desc()
        )
        .all()
    )

    project_deliveries = {}

    for delivery in all_deliveries:

        if delivery.project_id not in project_deliveries:

            project_deliveries[
                delivery.project_id
            ] = []

        project_deliveries[
            delivery.project_id
        ].append(delivery)

    # -----------------------------------------------------
    # LATEST DELIVERY PER PROJECT
    # -----------------------------------------------------

    latest_delivery_by_project = {}

    for project_id, deliveries in project_deliveries.items():

        if deliveries:

            latest_delivery_by_project[
                project_id
            ] = deliveries[0]

    # -----------------------------------------------------
    # CUSTOMER INTELLIGENCE
    # -----------------------------------------------------

    customer_stats = {}

    for customer in customers:

        projects = customer_projects.get(
            customer.id,
            []
        )

        # ---------------------------------------------
        # PROJECT STATUS COUNTS
        # ---------------------------------------------

        status_counts = {

            "Pending Assignment": 0,

            "Payment Pending": 0,

            "Assigned": 0,

            "In Progress": 0,

            "Submitted": 0,

            "Revision": 0,

            "Completed": 0,

            "Cancelled": 0

        }

        for project in projects:

            status = project.status

            if status in status_counts:

                status_counts[
                    status
                ] += 1

        # ---------------------------------------------
        # SERVICE COUNTS
        # ---------------------------------------------

        service_counts = {}

        for project in projects:

            service = project.service or "Other"

            service_counts[
                service
            ] = service_counts.get(
                service,
                0
            ) + 1

        # ---------------------------------------------
        # PACKAGE COUNTS
        # ---------------------------------------------

        package_counts = {}

        for project in projects:

            package = project.package or "Other"

            package_counts[
                package
            ] = package_counts.get(
                package,
                0
            ) + 1

        # ---------------------------------------------
        # FINANCIAL INFORMATION
        # ---------------------------------------------

        total_project_value = 0
        total_spent = 0
        paid_project_count = 0
        payment_pending_count = 0

        project_payment_data = {}

        for project in projects:

            package_price = PACKAGE_PRICES.get(
                project.package,
                0
            )

            total_project_value += package_price

            payment = latest_payment_by_project.get(
                project.id
            )

            payment_status = "Not Paid"

            if payment:

                payment_status = (
                    payment.status
                    or "Unknown"
                )

                if (
                    payment.status
                    and payment.status.lower()
                    == "paid"
                ):

                    total_spent += (
                        payment.amount
                        or package_price
                    )

                    paid_project_count += 1

            if (
                payment_status.lower()
                in [
                    "pending",
                    "created",
                    "payment pending"
                ]
            ):

                payment_pending_count += 1

            project_payment_data[
                project.id
            ] = payment

        # ---------------------------------------------
        # ACTIVE PROJECTS
        # ---------------------------------------------

        active_statuses = [
            "Pending Assignment",
            "Assigned",
            "In Progress",
            "Submitted",
            "Revision"
        ]

        active_project_count = sum(
            1
            for project in projects
            if project.status in active_statuses
        )

        # ---------------------------------------------
        # COMPLETED PROJECTS
        # ---------------------------------------------

        completed_project_count = sum(
            1
            for project in projects
            if project.status == "Completed"
        )

        # ---------------------------------------------
        # REVISION PROJECTS
        # ---------------------------------------------

        revision_project_count = sum(
            1
            for project in projects
            if project.status == "Revision"
        )

        # ---------------------------------------------
        # PROJECTS WITH DELIVERIES
        # ---------------------------------------------

        delivery_project_count = sum(
            1
            for project in projects
            if project.id in latest_delivery_by_project
        )

        # ---------------------------------------------
        # PROFESSIONALS USED BY CUSTOMER
        # ---------------------------------------------

        professionals_used = []

        for project in projects:

            professional = (
                assigned_professional_by_project.get(
                    project.id
                )
            )

            if professional:

                if professional not in professionals_used:

                    professionals_used.append(
                        professional
                    )

        # ---------------------------------------------
        # CUSTOMER STATS
        # ---------------------------------------------

        customer_stats[
            customer.id
        ] = {

            "total_projects":
                len(projects),

            "active_projects":
                active_project_count,

            "completed_projects":
                completed_project_count,

            "revision_projects":
                revision_project_count,

            "delivery_projects":
                delivery_project_count,

            "paid_projects":
                paid_project_count,

            "payment_pending_projects":
                payment_pending_count,

            "total_project_value":
                total_project_value,

            "total_spent":
                total_spent,

            "average_project_value":
                (
                    total_project_value / len(projects)
                    if projects
                    else 0
                ),

            "status_counts":
                status_counts,

            "service_counts":
                service_counts,

            "package_counts":
                package_counts,

            "professionals":
                professionals_used
        }

    # -----------------------------------------------------
    # SEND EVERYTHING TO ADMIN CUSTOMERS PAGE
    # -----------------------------------------------------

    return render_template(

        "admin_customers.html",

        customers=customers,

        customer_profiles=customer_profiles,

        customer_projects=customer_projects,

        customer_stats=customer_stats,

        latest_payment_by_project=
            latest_payment_by_project,

        project_payment_data=
            project_payment_data
            if "project_payment_data" in locals()
            else {},

        assigned_professional_by_project=
            assigned_professional_by_project,

        professional_profiles=
            professional_profiles,

        project_deliveries=
            project_deliveries,

        latest_delivery_by_project=
            latest_delivery_by_project
    )


# =========================================================
# ADMIN PROFESSIONALS
# =========================================================

@app.route("/admin/professionals")
@login_required
def admin_professionals():

    if current_user.role != "admin":
        flash("Admin access required.")
        return redirect(url_for("dashboard"))

    # -----------------------------------------------------
    # LOAD ALL PROFESSIONAL PROFILES
    # -----------------------------------------------------

    profiles = (
        ProfessionalProfile.query
        .order_by(
            ProfessionalProfile.created_at.desc()
        )
        .all()
    )

    # -----------------------------------------------------
    # PROFILE COMPLETION
    # -----------------------------------------------------

    completion_map = {}

    for profile in profiles:

        completion_map[profile.id] = (
            calculate_professional_profile_completion(
                profile
            )
        )

    # -----------------------------------------------------
    # PROFESSIONAL INTELLIGENCE
    #
    # This map contains project/application statistics
    # for every professional.
    # -----------------------------------------------------

    professional_stats = {}

    for profile in profiles:

        professional_id = profile.user_id

        # -------------------------------------------------
        # ALL APPLICATIONS
        # -------------------------------------------------

        applications = (
            ProfessionalProjectApplication.query
            .filter_by(
                professional_id=professional_id
            )
            .order_by(
                ProfessionalProjectApplication.created_at.desc()
            )
            .all()
        )

        # -------------------------------------------------
        # APPLICATION COUNTS
        # -------------------------------------------------

        total_applications = len(
            applications
        )

        applied_count = sum(
            1
            for application in applications
            if application.status == "Applied"
        )

        assigned_application_count = sum(
            1
            for application in applications
            if application.status == "Assigned"
        )

        not_selected_count = sum(
            1
            for application in applications
            if application.status == "Not Selected"
        )

        # -------------------------------------------------
        # PROJECTS ASSIGNED TO THIS PROFESSIONAL
        #
        # An assigned application identifies the
        # professional responsible for the project.
        # -------------------------------------------------

        assigned_applications = [
            application
            for application in applications
            if application.status == "Assigned"
        ]

        assigned_projects = []

        for application in assigned_applications:

            if application.project:
                assigned_projects.append(
                    application.project
                )

        # -------------------------------------------------
        # PROJECT STATUS COUNTS
        # -------------------------------------------------

        active_projects = [
            project
            for project in assigned_projects
            if project.status in [
                "Assigned",
                "In Progress",
                "Submitted",
                "Revision"
            ]
        ]

        in_progress_projects = [
            project
            for project in assigned_projects
            if project.status == "In Progress"
        ]

        submitted_projects = [
            project
            for project in assigned_projects
            if project.status == "Submitted"
        ]

        revision_projects = [
            project
            for project in assigned_projects
            if project.status == "Revision"
        ]

        completed_projects = [
            project
            for project in assigned_projects
            if project.status == "Completed"
        ]

        payment_pending_projects = [
            project
            for project in assigned_projects
            if project.status == "Payment Pending"
        ]

        # -------------------------------------------------
        # TOTAL PROJECTS
        # -------------------------------------------------

        total_assigned_projects = len(
            assigned_projects
        )

        active_project_count = len(
            active_projects
        )

        in_progress_count = len(
            in_progress_projects
        )

        submitted_count = len(
            submitted_projects
        )

        revision_count = len(
            revision_projects
        )

        completed_count = len(
            completed_projects
        )

        payment_pending_count = len(
            payment_pending_projects
        )

        # -------------------------------------------------
        # PROJECT HISTORY
        #
        # Keep newest projects first.
        # -------------------------------------------------

        project_history = sorted(
            assigned_projects,
            key=lambda project: (
                project.created_at
                if project.created_at
                else datetime.min
            ),
            reverse=True
        )

        # -------------------------------------------------
        # APPLICATION HISTORY
        # -------------------------------------------------

        application_history = applications

        # -------------------------------------------------
        # SERVICE BREAKDOWN
        # -------------------------------------------------

        website_project_count = sum(
            1
            for project in assigned_projects
            if project.service
            == "Website Design & Development"
        )

        seo_project_count = sum(
            1
            for project in assigned_projects
            if project.service == "SEO"
        )

        # -------------------------------------------------
        # REVISION / DELIVERY INFORMATION
        #
        # ProjectDelivery belongs to a project and
        # professional, so calculate submission history
        # for this professional.
        # -------------------------------------------------

        delivery_map = {}

        total_submissions = 0

        for project in assigned_projects:

            deliveries = (
                ProjectDelivery.query
                .filter_by(
                    project_id=project.id,
                    professional_id=professional_id
                )
                .order_by(
                    ProjectDelivery.submission_number.desc()
                )
                .all()
            )

            delivery_map[
                project.id
            ] = deliveries

            total_submissions += len(
                deliveries
            )

        # -------------------------------------------------
        # PROFESSIONAL PERFORMANCE
        # -------------------------------------------------

        completion_rate = 0

        if total_assigned_projects > 0:

            completion_rate = round(
                (
                    completed_count
                    / total_assigned_projects
                ) * 100
            )

        # -------------------------------------------------
        # STORE EVERYTHING FOR THIS PROFESSIONAL
        # -------------------------------------------------

        professional_stats[
            profile.id
        ] = {

            "professional_id":
                professional_id,

            "total_applications":
                total_applications,

            "applied_count":
                applied_count,

            "assigned_application_count":
                assigned_application_count,

            "not_selected_count":
                not_selected_count,

            "total_assigned_projects":
                total_assigned_projects,

            "active_project_count":
                active_project_count,

            "in_progress_count":
                in_progress_count,

            "submitted_count":
                submitted_count,

            "revision_count":
                revision_count,

            "completed_count":
                completed_count,

            "payment_pending_count":
                payment_pending_count,

            "website_project_count":
                website_project_count,

            "seo_project_count":
                seo_project_count,

            "total_submissions":
                total_submissions,

            "completion_rate":
                completion_rate,

            "assigned_projects":
                assigned_projects,

            "active_projects":
                active_projects,

            "completed_projects":
                completed_projects,

            "project_history":
                project_history,

            "application_history":
                application_history,

            "delivery_map":
                delivery_map
        }

    # -----------------------------------------------------
    # ADMIN PROFESSIONALS TEMPLATE
    # -----------------------------------------------------

    return render_template(
        "admin_professionals.html",

        profiles=profiles,

        completion_map=completion_map,

        professional_stats=professional_stats
    )


# =========================================================
# VERIFY PROFESSIONAL
# =========================================================

@app.route(
    "/admin/professionals/<int:profile_id>/verify",
    methods=["POST"]
)
@login_required
def verify_professional(profile_id):

    if current_user.role != "admin":

        flash(
            "Admin access required."
        )

        return redirect(
            url_for("dashboard")
        )

    profile = ProfessionalProfile.query.get_or_404(
        profile_id
    )

    profile.verification_status = "Verified"

    profile.verification_notes = (
        "Professional verified by admin."
    )

    db.session.commit()

    flash(
        "Professional verified successfully."
    )

    return redirect(
        url_for("admin_professionals")
    )


# =========================================================
# REJECT PROFESSIONAL
# =========================================================

@app.route(
    "/admin/professionals/<int:profile_id>/reject",
    methods=["POST"]
)
@login_required
def reject_professional(profile_id):

    if current_user.role != "admin":

        flash(
            "Admin access required."
        )

        return redirect(
            url_for("dashboard")
        )

    profile = ProfessionalProfile.query.get_or_404(
        profile_id
    )

    verification_notes = request.form.get(
        "verification_notes",
        ""
    ).strip()

    profile.verification_status = "Rejected"

    profile.verification_notes = (
        verification_notes
        or "Professional profile rejected by admin."
    )

    db.session.commit()

    flash(
        "Professional rejected."
    )

    return redirect(
        url_for("admin_professionals")
    )


# =========================================================
# ADMIN APPLICATIONS
# =========================================================

@app.route(
    "/admin/applications"
)
@login_required
def admin_applications():

    if current_user.role != "admin":

        flash(
            "Admin access required."
        )

        return redirect(
            url_for("dashboard")
        )

    applications = (
        ProfessionalProjectApplication.query
        .order_by(
            ProfessionalProjectApplication.created_at.desc()
        )
        .all()
    )

    return render_template(
        "admin_applications.html",
        applications=applications
    )


# =========================================================
# ASSIGN PROFESSIONAL
# =========================================================

@app.route(
    "/admin/applications/<int:application_id>/assign",
    methods=["POST"]
)
@login_required
def assign_professional(application_id):

    if current_user.role != "admin":

        flash(
            "Admin access required."
        )

        return redirect(
            url_for("dashboard")
        )

    application = (
        ProfessionalProjectApplication.query.get_or_404(
            application_id
        )
    )

    project = application.project

    if project.status != "Pending Assignment":

        flash(
            "This project is no longer available for assignment."
        )

        return redirect(
            url_for("admin_applications")
        )

    if application.status != "Applied":

        flash(
            "This application is no longer available for assignment."
        )

        return redirect(
            url_for("admin_applications")
        )

    # -----------------------------------------------------
    # ASSIGN SELECTED PROFESSIONAL
    # -----------------------------------------------------

    application.status = "Assigned"

    project.status = "Assigned"

    # -----------------------------------------------------
    # OTHER APPLICATIONS FOR SAME PROJECT
    # ARE NO LONGER ACTIVE
    # -----------------------------------------------------

    other_applications = (
        ProfessionalProjectApplication.query
        .filter(
            ProfessionalProjectApplication.project_id
            == project.id,
            ProfessionalProjectApplication.id
            != application.id,
            ProfessionalProjectApplication.status
            == "Applied"
        )
        .all()
    )

    for other_application in other_applications:

        other_application.status = "Not Selected"

    db.session.commit()

    flash(
        "Professional assigned successfully."
    )

    return redirect(
        url_for("admin_applications")
    )

# =========================================================
# ADMIN PROJECT MANAGEMENT
# =========================================================

@app.route(
    "/admin/project-management"
)
@login_required
def admin_project_management():

    if current_user.role != "admin":

        flash(
            "Admin access required."
        )

        return redirect(
            url_for("dashboard")
        )

    # -----------------------------------------------------
    # GET ALL PROJECTS
    # -----------------------------------------------------

    projects = (
        Project.query
        .order_by(
            Project.created_at.desc()
        )
        .all()
    )

    # -----------------------------------------------------
    # PAYMENT MAP
    #
    # Keep the latest payment attempt for every project.
    # -----------------------------------------------------

    payment_map = {}

    payments = (
        Payment.query
        .order_by(
            Payment.created_at.desc()
        )
        .all()
    )

    for payment in payments:

        if payment.project_id not in payment_map:

            payment_map[
                payment.project_id
            ] = payment

    # -----------------------------------------------------
    # ASSIGNMENT MAP
    #
    # Store the assigned application for every project.
    # -----------------------------------------------------

    assignment_map = {}

    assigned_applications = (
        ProfessionalProjectApplication.query
        .filter_by(
            status="Assigned"
        )
        .all()
    )

    for application in assigned_applications:

        assignment_map[
            application.project_id
        ] = application

    # -----------------------------------------------------
    # PROFESSIONAL MAP
    #
    # Store the actual User object for the assigned
    # professional.
    # -----------------------------------------------------

    professional_map = {}

    for project_id, application in assignment_map.items():

        if application.professional:

            professional_map[
                project_id
            ] = application.professional

    # -----------------------------------------------------
    # CUSTOMER PROFILE MAP
    # -----------------------------------------------------

    customer_profile_map = {}

    customer_profiles = (
        CustomerProfile.query
        .all()
    )

    for profile in customer_profiles:

        customer_profile_map[
            profile.user_id
        ] = profile

    # -----------------------------------------------------
    # LATEST DELIVERY MAP
    # -----------------------------------------------------

    delivery_map = {}

    deliveries = (
        ProjectDelivery.query
        .order_by(
            ProjectDelivery.submitted_at.desc()
        )
        .all()
    )

    for delivery in deliveries:

        if delivery.project_id not in delivery_map:

            delivery_map[
                delivery.project_id
            ] = delivery

    # -----------------------------------------------------
    # PROJECT STATISTICS
    # -----------------------------------------------------

    active_statuses = [
        "Pending Assignment",
        "Assigned",
        "In Progress",
        "Submitted",
        "Revision"
    ]

    active_project_count = sum(
        1
        for project in projects
        if project.status in active_statuses
    )

    submitted_project_count = sum(
        1
        for project in projects
        if project.status == "Submitted"
    )

    completed_project_count = sum(
        1
        for project in projects
        if project.status == "Completed"
    )

    # -----------------------------------------------------
    # RENDER ADMIN PROJECT MANAGEMENT
    # -----------------------------------------------------

    return render_template(
        "admin_project_management.html",

        projects=projects,

        payment_map=payment_map,

        assignment_map=assignment_map,

        professional_map=professional_map,

        delivery_map=delivery_map,

        customer_profile_map=customer_profile_map,

        active_project_count=
            active_project_count,

        submitted_project_count=
            submitted_project_count,

        completed_project_count=
            completed_project_count
    )

# =========================================================
# ADMIN PROJECT REVIEW
# =========================================================

@app.route("/admin/project-review")
@login_required

def admin_project_review():
    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("dashboard"))

    projects = (
        Project.query
        .order_by(Project.created_at.desc())
        .all()
    )

    # Get the latest delivery for every project.
    # The admin project-review template expects a dictionary
    # keyed by project.id.
    project_deliveries = {}

    for project in projects:
        latest_delivery = (
            ProjectDelivery.query
            .filter_by(project_id=project.id)
            .order_by(ProjectDelivery.submission_number.desc())
            .first()
        )

        project_deliveries[project.id] = latest_delivery

    # Get the assigned professional/application for every project.
    project_applications = {}

    for project in projects:
        assigned_application = (
            ProfessionalProjectApplication.query
            .filter_by(
                project_id=project.id,
                status="Assigned"
            )
            .first()
        )

        project_applications[project.id] = assigned_application

    return render_template(
        "admin_project_review.html",
        projects=projects,
        project_deliveries=project_deliveries,
        project_applications=project_applications
    )


# =========================================================
# REQUEST PROJECT REVISION
# =========================================================

@app.route(
    "/admin/project/<int:project_id>/revision",
    methods=["POST"]
)
@login_required
def request_project_revision(project_id):

    if current_user.role != "admin":

        flash(
            "Admin access required."
        )

        return redirect(
            url_for("dashboard")
        )

    project = Project.query.get_or_404(
        project_id
    )

    if project.status != "Submitted":

        flash(
            "Only submitted projects can be sent for revision."
        )

        return redirect(
            url_for("admin_project_review")
        )

    revision_comment = request.form.get(
        "revision_comment",
        ""
    ).strip()

    if not revision_comment:

        flash(
            "Please provide a revision comment."
        )

        return redirect(
            url_for("admin_project_review")
        )

    latest_delivery = get_latest_project_delivery(
        project.id
    )

    if not latest_delivery:

        flash(
            "No delivery was found for this project."
        )

        return redirect(
            url_for("admin_project_review")
        )

    latest_delivery.status = "Revision"

    latest_delivery.review_comment = (
        revision_comment
    )

    latest_delivery.reviewed_at = (
        get_ist_now()
    )

    project.status = "Revision"

    project.revision_comment = (
        revision_comment
    )

    db.session.commit()

    flash(
        "Revision requested successfully."
    )

    return redirect(
        url_for("admin_project_review")
    )


# =========================================================
# APPROVE PROJECT
# =========================================================

@app.route(
    "/admin/project/<int:project_id>/approve",
    methods=["POST"]
)
@login_required
def approve_project(project_id):

    if current_user.role != "admin":

        flash(
            "Admin access required."
        )

        return redirect(
            url_for("dashboard")
        )

    project = Project.query.get_or_404(
        project_id
    )

    if project.status != "Submitted":

        flash(
            "Only submitted projects can be approved."
        )

        return redirect(
            url_for("admin_project_review")
        )

    latest_delivery = get_latest_project_delivery(
        project.id
    )

    if not latest_delivery:

        flash(
            "No delivery was found for this project."
        )

        return redirect(
            url_for("admin_project_review")
        )

    latest_delivery.status = "Approved"

    latest_delivery.reviewed_at = (
        get_ist_now()
    )

    project.status = "Completed"

    project.revision_comment = None

    db.session.commit()

    flash(
        "Project approved and marked as completed."
    )

    return redirect(
        url_for("admin_project_review")
    )

# ============================================================
# CUSTOMER BUSINESS MANAGEMENT
# ============================================================

@app.route("/businesses")
@login_required
def businesses():
    if current_user.role != "customer":
        flash("Access denied.", "danger")
        return redirect(url_for("dashboard"))

    customer_businesses = (
        Business.query
        .filter_by(customer_id=current_user.id)
        .order_by(Business.created_at.asc())
        .all()
    )

    return render_template(
        "businesses.html",
        businesses=customer_businesses
    )


@app.route("/business/add", methods=["GET", "POST"])
@login_required
def add_business():
    if current_user.role != "customer":
        flash("Access denied.", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        business_type = request.form.get("business_type", "").strip()
        location = request.form.get("location", "").strip()
        website = request.form.get("website", "").strip()
        social_links = request.form.get("social_links", "").strip()
        description = request.form.get("description", "").strip()
        target_audience = request.form.get("target_audience", "").strip()
        goals = request.form.get("goals", "").strip()
        preferred_budget = request.form.get("preferred_budget", "").strip()

        # Required field
        if not name:
            flash("Business name is required.", "danger")
            return render_template("add_business.html")

        # Website validation
        if website and not is_valid_http_url(website):
            flash(
                "Please enter a valid website URL beginning with http:// or https://.",
                "danger"
            )
            return render_template(
                "add_business.html",
                form_data=request.form
            )

        business = Business(
            customer_id=current_user.id,
            name=name,
            business_type=business_type or None,
            location=location or None,
            website=website or None,
            social_links=social_links or None,
            description=description or None,
            target_audience=target_audience or None,
            goals=goals or None,
            preferred_budget=preferred_budget or None
        )

        db.session.add(business)
        db.session.commit()

        flash(
            f"Business '{business.name}' was added successfully.",
            "success"
        )

        return redirect(url_for("business_details", business_id=business.id))

    return render_template("add_business.html")


@app.route("/business/<int:business_id>")
@login_required
def business_details(business_id):
    if current_user.role != "customer":
        flash("Access denied.", "danger")
        return redirect(url_for("dashboard"))

    business = (
        Business.query
        .filter_by(
            id=business_id,
            customer_id=current_user.id
        )
        .first()
    )

    if not business:
        flash("Business not found.", "danger")
        return redirect(url_for("businesses"))

    projects = (
        Project.query
        .filter_by(
            customer_id=current_user.id,
            business_id=business.id
        )
        .order_by(Project.created_at.desc())
        .all()
    )

    return render_template(
        "business_details.html",
        business=business,
        projects=projects
    )
@app.route("/business/<int:business_id>/edit", methods=["GET", "POST"])
@login_required
def edit_business(business_id):

    if current_user.role != "customer":
        flash("Access denied.", "danger")
        return redirect(url_for("dashboard"))

    business = (
        Business.query
        .filter_by(
            id=business_id,
            customer_id=current_user.id
        )
        .first()
    )

    if not business:
        flash("Business not found.", "danger")
        return redirect(url_for("businesses"))

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        business_type = request.form.get(
            "business_type",
            ""
        ).strip()
        location = request.form.get(
            "location",
            ""
        ).strip()
        website = request.form.get(
            "website",
            ""
        ).strip()
        social_links = request.form.get(
            "social_links",
            ""
        ).strip()
        description = request.form.get(
            "description",
            ""
        ).strip()
        target_audience = request.form.get(
            "target_audience",
            ""
        ).strip()
        goals = request.form.get(
            "goals",
            ""
        ).strip()
        preferred_budget = request.form.get(
            "preferred_budget",
            ""
        ).strip()

        if not name:
            flash(
                "Business name is required.",
                "danger"
            )

            return render_template(
                "edit_business.html",
                business=business,
                form_data=request.form
            )

        if website and not is_valid_http_url(website):
            flash(
                "Please enter a valid website URL beginning with http:// or https://.",
                "danger"
            )

            return render_template(
                "edit_business.html",
                business=business,
                form_data=request.form
            )

        business.name = name
        business.business_type = business_type or None
        business.location = location or None
        business.website = website or None
        business.social_links = social_links or None
        business.description = description or None
        business.target_audience = target_audience or None
        business.goals = goals or None
        business.preferred_budget = preferred_budget or None

        db.session.commit()

        flash(
            f"Business '{business.name}' was updated successfully.",
            "success"
        )

        return redirect(
            url_for(
                "business_details",
                business_id=business.id
            )
        )

    return render_template(
        "edit_business.html",
        business=business
    )


@app.route(
    "/business/<int:business_id>/delete",
    methods=["POST"]
)
@login_required
def delete_business(business_id):

    if current_user.role != "customer":
        flash("Access denied.", "danger")
        return redirect(url_for("dashboard"))

    business = (
        Business.query
        .filter_by(
            id=business_id,
            customer_id=current_user.id
        )
        .first()
    )

    if not business:
        flash("Business not found.", "danger")
        return redirect(url_for("businesses"))

    project_count = (
        Project.query
        .filter_by(
            customer_id=current_user.id,
            business_id=business.id
        )
        .count()
    )

    if project_count > 0:
        flash(
            "This business cannot be deleted because it has existing projects. "
            "You can edit the business details instead.",
            "danger"
        )

        return redirect(
            url_for(
                "business_details",
                business_id=business.id
            )
        )

    business_name = business.name

    db.session.delete(business)
    db.session.commit()

    flash(
        f"Business '{business_name}' was deleted successfully.",
        "success"
    )

    return redirect(url_for("businesses"))

# =========================================================
# LEGACY START PROJECT
# =========================================================

@app.route(
    "/start-project/<service_slug>",
    methods=["GET", "POST"]
)
@login_required
def start_project(service_slug):

    if current_user.role != "customer":

        return redirect(
            url_for("dashboard")
        )

    service = next(
        (
            item
            for item in services
            if item["slug"] == service_slug
        ),
        None
    )

    if not service:

        flash(
            "Service not found.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    # -----------------------------------------------------
    # LOAD CUSTOMER BUSINESSES
    # -----------------------------------------------------

    customer_businesses = (
        Business.query
        .filter_by(
            customer_id=current_user.id
        )
        .order_by(
            Business.created_at.asc(),
            Business.id.asc()
        )
        .all()
    )

    selected_business_id = request.args.get(
        "business_id",
        type=int
    )

    # -----------------------------------------------------
    # POST
    # -----------------------------------------------------

    if request.method == "POST":

        package = request.form.get(
            "package",
            ""
        ).strip()

        requirements_text = request.form.get(
            "requirements",
            ""
        ).strip()

        business_id = request.form.get(
            "business_id",
            type=int
        )

        # -------------------------------------------------
        # VALIDATE BUSINESS
        # -------------------------------------------------

        business = get_business_for_customer(
            business_id,
            current_user.id
        )

        if not business:

            flash(
                "Please select a valid business.",
                "danger"
            )

            return redirect(
                url_for(
                    "start_project",
                    service_slug=service_slug
                )
            )

        # -------------------------------------------------
        # VALIDATE PACKAGE
        # -------------------------------------------------

        if not package:

            flash(
                "Please select a package.",
                "danger"
            )

            return redirect(
                url_for(
                    "start_project",
                    service_slug=service_slug,
                    business_id=business.id
                )
            )

        # -------------------------------------------------
        # VALIDATE REQUIREMENTS
        # -------------------------------------------------

        if not requirements_text:

            flash(
                "Please provide your project requirements.",
                "danger"
            )

            return redirect(
                url_for(
                    "start_project",
                    service_slug=service_slug,
                    business_id=business.id
                )
            )

        # -------------------------------------------------
        # VALIDATE PACKAGE
        # -------------------------------------------------

        valid_package = any(
            item["name"] == package
            for item in service["packages"]
        )

        if not valid_package:

            flash(
                "Invalid package selected.",
                "danger"
            )

            return redirect(
                url_for(
                    "start_project",
                    service_slug=service_slug,
                    business_id=business.id
                )
            )

        # -------------------------------------------------
        # CREATE PROJECT
        # -------------------------------------------------

        project = Project(
            customer_id=current_user.id,
            business_id=business.id,
            service=service["name"],
            package=package,
            requirements=requirements_text,
            status="Pending Assignment"
        )

        db.session.add(
            project
        )

        db.session.commit()

        flash(
            "Project created successfully.",
            "success"
        )

        return redirect(
            url_for(
                "project_details",
                project_id=project.id
            )
        )

    # -----------------------------------------------------
    # GET
    # -----------------------------------------------------

    return render_template(
        "start_project.html",
        service=service,
        businesses=customer_businesses,
        selected_business_id=selected_business_id
    )


# =========================================================
# REQUIREMENTS
# =========================================================

@app.route(
    "/requirements/<service_slug>",
    methods=["GET", "POST"]
)
@login_required
def requirements(service_slug):

    if current_user.role != "customer":

        return redirect(
            url_for("dashboard")
        )

    service = next(
        (
            item
            for item in services
            if item["slug"] == service_slug
        ),
        None
    )

    if not service:

        flash(
            "Service not found.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    # -----------------------------------------------------
    # GET BUSINESS ID FROM URL
    # -----------------------------------------------------

    selected_business_id = request.args.get(
        "business_id",
        type=int
    )

    # -----------------------------------------------------
    # VERIFY BUSINESS BELONGS TO CURRENT CUSTOMER
    # -----------------------------------------------------

    business = get_business_for_customer(
        selected_business_id,
        current_user.id
    )

    if not business:

        flash(
            "Please select a valid business.",
            "danger"
        )

        return redirect(
            url_for(
                "businesses"
            )
        )

    selected_package = request.args.get(
        "package",
        ""
    ).strip()

    # -----------------------------------------------------
    # POST
    # -----------------------------------------------------

    if request.method == "POST":

        package = request.form.get(
            "package",
            selected_package
        ).strip()

        requirements_text = request.form.get(
            "requirements",
            ""
        ).strip()

        # Get business ID from submitted form
        business_id = request.form.get(
            "business_id",
            selected_business_id,
            type=int
        )

        # Verify ownership again
        business = get_business_for_customer(
            business_id,
            current_user.id
        )

        if not business:

            flash(
                "Please select a valid business.",
                "danger"
            )

            return redirect(
                url_for(
                    "requirements",
                    service_slug=service_slug,
                    package=package,
                    business_id=selected_business_id
                )
            )

        # -------------------------------------------------
        # PACKAGE VALIDATION
        # -------------------------------------------------

        if not package:

            flash(
                "Please select a package.",
                "danger"
            )

            return redirect(
                url_for(
                    "requirements",
                    service_slug=service_slug,
                    business_id=business.id
                )
            )

        # -------------------------------------------------
        # REQUIREMENTS VALIDATION
        # -------------------------------------------------

        if not requirements_text:

            flash(
                "Please provide your project requirements.",
                "danger"
            )

            return redirect(
                url_for(
                    "requirements",
                    service_slug=service_slug,
                    package=package,
                    business_id=business.id
                )
            )

        # -------------------------------------------------
        # VALIDATE PACKAGE BELONGS TO SERVICE
        # -------------------------------------------------

        valid_package = any(
            item["name"] == package
            for item in service["packages"]
        )

        if not valid_package:

            flash(
                "Invalid package selected.",
                "danger"
            )

            return redirect(
                url_for(
                    "requirements",
                    service_slug=service_slug,
                    business_id=business.id
                )
            )

        # -------------------------------------------------
        # CREATE PROJECT WITH BUSINESS
        # -------------------------------------------------

        project = Project(
            customer_id=current_user.id,
            business_id=business.id,
            service=service["name"],
            package=package,
            requirements=requirements_text,
            status="Payment Pending"
        )

        db.session.add(
            project
        )

        db.session.commit()

        # -------------------------------------------------
        # GO TO PAYMENT
        # -------------------------------------------------

        return redirect(
            url_for(
                "payment_page",
                project_id=project.id
            )
        )

    # -----------------------------------------------------
    # GET REQUIREMENTS PAGE
    # -----------------------------------------------------

    return render_template(
        "requirements.html",
        service=service,
        selected_package=selected_package,
        business=business,
        selected_business_id=business.id
    )


# =========================================================
# CREATE RAZORPAY PAYMENT ORDER
# =========================================================

@app.route(
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

@app.route(
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

@app.route(
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

@app.route(
    "/api/services"
)
def api_services():

    return jsonify(
        services
    )


# =========================================================
# SINGLE SERVICE API
# =========================================================

@app.route(
    "/api/service/<slug>"
)
def api_service(slug):

    service = next(
        (
            item
            for item in services
            if item["slug"] == slug
        ),
        None
    )

    if not service:

        return jsonify({
            "success": False,
            "message": "Service not found."
        }), 404

    return jsonify(
        service
    )


# ============================================================
# DATABASE INITIALIZATION + SAFE MIGRATION
# ============================================================

with app.app_context():
    # --------------------------------------------------------
    # 1. Create all tables that do not already exist
    # --------------------------------------------------------
    db.create_all()

    inspector = db.inspect(db.engine)

    # --------------------------------------------------------
    # 2. Make sure the Business table exists
    # --------------------------------------------------------
    table_names = inspector.get_table_names()

    if "business" not in table_names:
        Business.__table__.create(
            bind=db.engine,
            checkfirst=True
        )

    # Refresh inspector after possible table creation
    inspector = db.inspect(db.engine)

    # --------------------------------------------------------
    # 3. Add business_id to existing project table
    # --------------------------------------------------------
    if "project" in inspector.get_table_names():

        project_columns = {
            column["name"]
            for column in inspector.get_columns("project")
        }

        if "business_id" not in project_columns:
            with db.engine.begin() as connection:
                connection.execute(
                    db.text(
                        "ALTER TABLE project ADD COLUMN business_id INTEGER"
                    )
                )

            print("Added project.business_id successfully.")

    # --------------------------------------------------------
    # 4. Add paid_at to existing payment table if missing
    # --------------------------------------------------------
    inspector = db.inspect(db.engine)

    if "payment" in inspector.get_table_names():

        payment_columns = {
            column["name"]
            for column in inspector.get_columns("payment")
        }

        if "paid_at" not in payment_columns:
            with db.engine.begin() as connection:
                connection.execute(
                    db.text(
                        "ALTER TABLE payment ADD COLUMN paid_at DATETIME"
                    )
                )

            print("Added payment.paid_at successfully.")

    # --------------------------------------------------------
    # 5. Refresh database metadata
    # --------------------------------------------------------
    inspector = db.inspect(db.engine)

    # --------------------------------------------------------
    # 6. Create default Business records for existing customers
    # --------------------------------------------------------
    customers = User.query.filter_by(role="customer").all()

    for customer in customers:

        # Find an existing business
        business = (
            Business.query
            .filter_by(customer_id=customer.id)
            .order_by(
                Business.created_at.asc(),
                Business.id.asc()
            )
            .first()
        )

        # Existing customer profile
        profile = (
            CustomerProfile.query
            .filter_by(user_id=customer.id)
            .first()
        )

        # ----------------------------------------------------
        # Create Business only when useful information exists
        # ----------------------------------------------------
        if not business:

            has_profile_business_data = False

            if profile:
                profile_values = [
                    profile.business_name,
                    profile.business_type,
                    profile.location,
                    profile.website,
                    profile.social_links,
                    profile.business_description,
                    profile.target_audience,
                    profile.business_goals,
                    profile.preferred_budget
                ]

                has_profile_business_data = any(
                    value and str(value).strip()
                    for value in profile_values
                )

            existing_projects = (
                Project.query
                .filter_by(customer_id=customer.id)
                .all()
            )

            # Create a default business if the customer already
            # has business information or existing projects.
            if has_profile_business_data or existing_projects:

                business_name = (
                    profile.business_name.strip()
                    if profile
                    and profile.business_name
                    and profile.business_name.strip()
                    else f"{customer.name}'s Business"
                )

                business = Business(
                    customer_id=customer.id,
                    name=business_name,
                    business_type=(
                        profile.business_type
                        if profile
                        else None
                    ),
                    location=(
                        profile.location
                        if profile
                        else None
                    ),
                    website=(
                        profile.website
                        if profile
                        else None
                    ),
                    social_links=(
                        profile.social_links
                        if profile
                        else None
                    ),
                    description=(
                        profile.business_description
                        if profile
                        else None
                    ),
                    target_audience=(
                        profile.target_audience
                        if profile
                        else None
                    ),
                    goals=(
                        profile.business_goals
                        if profile
                        else None
                    ),
                    preferred_budget=(
                        profile.preferred_budget
                        if profile
                        else None
                    )
                )

                db.session.add(business)
                db.session.flush()

                print(
                    f"Created default business for customer "
                    f"{customer.id}: {business.name}"
                )

        # ----------------------------------------------------
        # 7. Attach existing projects to the customer's
        #    default/first business
        # ----------------------------------------------------
        if business:

            existing_projects = (
                Project.query
                .filter_by(
                    customer_id=customer.id
                )
                .all()
            )

            for project in existing_projects:

                if project.business_id is None:
                    project.business_id = business.id

    # --------------------------------------------------------
    # 8. Commit all migration changes
    # --------------------------------------------------------
    db.session.commit()

    print("==============================================")
    print("AgencyOS database migration completed.")
    print("Existing data has been preserved.")
    print("Business structure is ready.")
    print("==============================================")


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":
    if os.getenv("ALLOW_LEGACY_APP") != "1":
        raise SystemExit("Legacy app execution is disabled by default. Set ALLOW_LEGACY_APP=1 to opt in (risky).")
    from app.config import resolve_flask_env
    _legacy_env = resolve_flask_env()
    app.run(debug=(_legacy_env == "development"))
