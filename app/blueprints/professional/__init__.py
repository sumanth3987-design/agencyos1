from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models import (
    User, ProfessionalProfile, Project, ProfessionalProjectApplication,
    ProjectDelivery, get_ist_now, is_valid_http_url,
    calculate_professional_profile_completion, professional_has_expertise,
    get_assigned_professional_application, get_latest_project_delivery
)
import json

professional_bp = Blueprint("professional", __name__)

@professional_bp.route(
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

@professional_bp.route(
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

@professional_bp.route(
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

@professional_bp.route(
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

@professional_bp.route(
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

@professional_bp.route(
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

@professional_bp.route(
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

@professional_bp.route(
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

@professional_bp.route(
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


