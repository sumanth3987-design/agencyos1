from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db, limiter
from app.models import (
    User, CustomerProfile, Business, ProfessionalProfile, Project, Payment,
    ProfessionalProjectApplication, ProjectDelivery, get_ist_now, PACKAGE_PRICES,
    calculate_professional_profile_completion, get_latest_project_delivery
)
from datetime import datetime

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/admin/dashboard")
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

@admin_bp.route(
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

@admin_bp.route("/admin/professionals")
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

@admin_bp.route(
    "/admin/professionals/<int:profile_id>/verify",
    methods=["POST"]
)
@limiter.limit("20 per minute")
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

@admin_bp.route(
    "/admin/professionals/<int:profile_id>/reject",
    methods=["POST"]
)
@limiter.limit("20 per minute")
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

@admin_bp.route(
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

@admin_bp.route(
    "/admin/applications/<int:application_id>/assign",
    methods=["POST"]
)
@limiter.limit("20 per minute")
@login_required
def assign_professional(application_id):

    if current_user.role != "admin":
        flash("Admin access required.")
        return redirect(url_for("dashboard"))

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
        return redirect(url_for("admin_applications"))

    if application.status != "Applied":
        flash(
            "This application is no longer available for assignment."
        )
        return redirect(url_for("admin_applications"))

    # -----------------------------------------------------
    # VERIFY PROFESSIONAL BEFORE CHANGING ANY STATE
    # -----------------------------------------------------

    professional = application.professional

    if professional is None:
        flash(
            "Cannot assign this project: professional account not found.",
            "warning"
        )
        return redirect(url_for("admin_applications"))

    professional_profile = getattr(
        professional,
        "professional_profile",
        None,
    )

    if (
        professional_profile is None
        or professional_profile.verification_status != "Verified"
    ):
        flash(
            "Professional profile must be verified before assignment.",
            "warning"
        )
        return redirect(url_for("admin_applications"))

    # -----------------------------------------------------
    # ASSIGN SELECTED PROFESSIONAL
    # -----------------------------------------------------

    application.status = "Assigned"
    project.status = "Assigned"

    # -----------------------------------------------------
    # MARK OTHER APPLICATIONS AS NOT SELECTED
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

    flash("Professional assigned successfully.")

    return redirect(url_for("admin_applications"))

# =========================================================
# ADMIN PROJECT MANAGEMENT
# =========================================================

@admin_bp.route(
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

@admin_bp.route("/admin/project-review")
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

@admin_bp.route(
    "/admin/project/<int:project_id>/revision",
    methods=["POST"]
)
@limiter.limit("20 per minute")
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

@admin_bp.route(
    "/admin/project/<int:project_id>/approve",
    methods=["POST"]
)
@limiter.limit("20 per minute")
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


