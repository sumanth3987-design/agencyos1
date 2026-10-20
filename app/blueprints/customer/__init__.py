from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models import (
    User, CustomerProfile, Business, ProfessionalProfile, Project, Payment,
    ProfessionalProjectApplication, ProjectDelivery, get_ist_now, is_valid_http_url,
    PACKAGE_PRICES, services, calculate_customer_profile_completion,
    get_business_for_customer, get_latest_project_delivery
)

customer_bp = Blueprint("customer", __name__)

@customer_bp.route(
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

@customer_bp.route("/dashboard")
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

@customer_bp.route(
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



@customer_bp.route("/businesses")
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


@customer_bp.route("/business/add", methods=["GET", "POST"])
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


@customer_bp.route("/business/<int:business_id>")
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
@customer_bp.route("/business/<int:business_id>/edit", methods=["GET", "POST"])
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


@customer_bp.route(
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

@customer_bp.route(
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

@customer_bp.route(
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


