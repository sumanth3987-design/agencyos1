import csv
from io import StringIO
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response
from flask_login import login_required, current_user
from app.extensions import db, limiter

# 1. CREATE BLUEPRINT (Must be defined first before any @admin_bp.route)
admin_bp = Blueprint("admin", __name__)

# 2. IMPORT ALL MODELS & UTILITIES
from app.models import (
    User, CustomerProfile, Business, ProfessionalProfile, Project, Payment,
    ProfessionalProjectApplication, ProjectDelivery, get_ist_now, PACKAGE_PRICES,
    calculate_professional_profile_completion, get_latest_project_delivery,
    Invoice, Notification
)


# =========================================================
# ADMIN EXECUTIVE DASHBOARD (WITH PAGINATION & FILTERS)
# =========================================================

@admin_bp.route("/admin/dashboard")
@admin_bp.route("/admin")
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        flash("Admin access required.", "danger")
        return redirect(url_for("dashboard"))

    # Pagination & Filtering Parameters
    page = request.args.get('page', 1, type=int)
    per_page = 15  # Shows 15 projects per page, supporting navigation for 25+
    status_filter = request.args.get('status', 'all')
    search_query = request.args.get('search', '', type=str)

    # Base query for metrics counters
    customer_count = User.query.filter_by(role="customer").count()
    professional_count = User.query.filter_by(role="professional").count()
    project_count = Project.query.count()

    pending_project_count = Project.query.filter_by(status="Pending Assignment").count()
    pending_verification_count = ProfessionalProfile.query.filter_by(verification_status="Pending").count()
    application_count = ProfessionalProjectApplication.query.count()

    submitted_project_count = Project.query.filter_by(status="Submitted").count()
    in_progress_project_count = Project.query.filter_by(status="In Progress").count()
    completed_project_count = Project.query.filter_by(status="Completed").count()
    payment_pending_project_count = Project.query.filter_by(status="Payment Pending").count()
    assigned_project_count = Project.query.filter_by(status="Assigned").count()
    revision_project_count = Project.query.filter_by(status="Revision").count()

    # Query setup for Management Directory / Active Projects list
    query = Project.query

    # Apply Status Filter
    if status_filter != 'all':
        query = query.filter(Project.status == status_filter)

    # Apply Search Filter (searches title or description)
    if search_query:
        search_term = f"%{search_query}%"
        query = query.filter(
            db.or_(
                Project.title.ilike(search_term),
                Project.description.ilike(search_term)
            )
        )

    # Paginate results
    pagination = query.order_by(Project.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    recent_projects = pagination.items

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
        recent_projects=recent_projects,
        pagination=pagination,
        current_status=status_filter,
        search_query=search_query
    )


# =========================================================
# ADMIN CUSTOMERS / CLIENT CRM
# =========================================================

@admin_bp.route("/admin/customers")
@login_required
def admin_customers():
    if current_user.role != "admin":
        flash("Admin access required.", "danger")
        return redirect(url_for("dashboard"))

    customers = User.query.filter_by(role="customer").order_by(User.created_at.desc()).all()
    all_projects = Project.query.order_by(Project.created_at.desc()).all()

    customer_profiles = {}
    customer_projects = {c.id: [] for c in customers}

    for c in customers:
        customer_profiles[c.id] = CustomerProfile.query.filter_by(user_id=c.id).first()

    for p in all_projects:
        if p.customer_id in customer_projects:
            customer_projects[p.customer_id].append(p)

    return render_template(
        "admin_customers.html",
        customers=customers,
        customer_profiles=customer_profiles,
        customer_projects=customer_projects
    )


# =========================================================
# ADMIN PROFESSIONALS / SPECIALISTS
# =========================================================

@admin_bp.route("/admin/professionals")
@login_required
def admin_professionals():
    if current_user.role != "admin":
        flash("Admin access required.", "danger")
        return redirect(url_for("dashboard"))

    profiles = ProfessionalProfile.query.order_by(ProfessionalProfile.created_at.desc()).all()
    completion_map = {p.id: calculate_professional_profile_completion(p) for p in profiles}

    return render_template(
        "admin_professionals.html",
        profiles=profiles,
        completion_map=completion_map
    )


@admin_bp.route("/admin/professionals/<int:profile_id>/verify", methods=["POST"])
@login_required
def verify_professional(profile_id):
    if current_user.role != "admin":
        flash("Admin access required.", "danger")
        return redirect(url_for("dashboard"))

    profile = ProfessionalProfile.query.get_or_404(profile_id)
    profile.verification_status = "Verified"
    profile.verification_notes = "Verified by admin."
    db.session.commit()

    flash("Specialist verified successfully.", "success")
    return redirect(url_for("admin.admin_professionals"))


@admin_bp.route("/admin/professionals/<int:profile_id>/reject", methods=["POST"])
@login_required
def reject_professional(profile_id):
    if current_user.role != "admin":
        flash("Admin access required.", "danger")
        return redirect(url_for("dashboard"))

    profile = ProfessionalProfile.query.get_or_404(profile_id)
    profile.verification_status = "Rejected"
    db.session.commit()

    flash("Specialist onboarding rejected.", "warning")
    return redirect(url_for("admin.admin_professionals"))


# =========================================================
# TALENT APPLICATIONS
# =========================================================

@admin_bp.route("/admin/applications")
@login_required
def admin_applications():
    if current_user.role != "admin":
        flash("Admin access required.", "danger")
        return redirect(url_for("dashboard"))

    applications = ProfessionalProjectApplication.query.order_by(
        ProfessionalProjectApplication.created_at.desc()
    ).all()

    return render_template("admin_applications.html", applications=applications)


@admin_bp.route("/admin/applications/<int:application_id>/assign", methods=["POST"])
@login_required
def assign_professional(application_id):
    if current_user.role != "admin":
        flash("Admin access required.", "danger")
        return redirect(url_for("dashboard"))

    app = ProfessionalProjectApplication.query.get_or_404(application_id)
    project = app.project

    if project.status != "Pending Assignment" or app.status != "Applied":
        flash("This project or application is no longer eligible for assignment.", "warning")
        return redirect(url_for("admin.admin_applications"))

    app.status = "Assigned"
    project.status = "Assigned"

    # Reject other applications for the same project
    other_apps = ProfessionalProjectApplication.query.filter(
        ProfessionalProjectApplication.project_id == project.id,
        ProfessionalProjectApplication.id != app.id,
        ProfessionalProjectApplication.status == "Applied"
    ).all()
    for o in other_apps:
        o.status = "Not Selected"

    db.session.commit()
    flash("Specialist successfully assigned to project.", "success")
    return redirect(url_for("admin.admin_applications"))


# =========================================================
# PROJECT MANAGEMENT & KANBAN
# =========================================================

@admin_bp.route("/admin/project-management")
@login_required
def admin_project_management():
    if current_user.role != "admin":
        flash("Admin access required.", "danger")
        return redirect(url_for("dashboard"))

    projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template("admin_project_management.html", projects=projects)


# =========================================================
# PROJECT REVIEW GATE
# =========================================================

@admin_bp.route("/admin/project-review")
@login_required
def admin_project_review():
    if current_user.role != "admin":
        flash("Admin access required.", "danger")
        return redirect(url_for("dashboard"))

    projects = Project.query.order_by(Project.created_at.desc()).all()
    project_deliveries = {}
    project_applications = {}

    for p in projects:
        latest = (
            ProjectDelivery.query
            .filter_by(project_id=p.id)
            .order_by(ProjectDelivery.submission_number.desc())
            .first()
        )
        project_deliveries[p.id] = latest

        assigned_app = ProfessionalProjectApplication.query.filter_by(
            project_id=p.id, status="Assigned"
        ).first()
        project_applications[p.id] = assigned_app

    return render_template(
        "admin_project_review.html",
        projects=projects,
        project_deliveries=project_deliveries,
        project_applications=project_applications
    )


@admin_bp.route("/admin/project/<int:project_id>/revision", methods=["POST"])
@login_required
def request_project_revision(project_id):
    if current_user.role != "admin":
        flash("Admin access required.", "danger")
        return redirect(url_for("dashboard"))

    project = Project.query.get_or_404(project_id)
    comment = request.form.get("revision_comment", "").strip()

    if not comment:
        flash("Please provide a revision comment.", "warning")
        return redirect(url_for("admin.admin_project_review"))

    latest_delivery = get_latest_project_delivery(project.id)
    if latest_delivery:
        latest_delivery.status = "Revision"
        latest_delivery.review_comment = comment
        latest_delivery.reviewed_at = get_ist_now()

    project.status = "Revision"
    project.revision_comment = comment
    db.session.commit()

    flash("Revision requested successfully.", "warning")
    return redirect(url_for("admin.admin_project_review"))


@admin_bp.route("/admin/project/<int:project_id>/approve", methods=["POST"])
@login_required
def approve_project(project_id):
    if current_user.role != "admin":
        flash("Admin access required.", "danger")
        return redirect(url_for("dashboard"))

    project = Project.query.get_or_404(project_id)
    latest_delivery = get_latest_project_delivery(project.id)
    if latest_delivery:
        latest_delivery.status = "Approved"
        latest_delivery.reviewed_at = get_ist_now()

    project.status = "Completed"
    project.revision_comment = None
    db.session.commit()

    flash("Project deliverable approved and marked as Completed.", "success")
    return redirect(url_for("admin.admin_project_review"))


# =========================================================
# NEW MANAGEMENT ACTIONS: UNASSIGN & DELETE
# =========================================================

@admin_bp.route("/admin/project/<int:project_id>/unassign", methods=["POST"])
@login_required
def unassign_professional(project_id):
    if current_user.role != "admin":
        flash("Admin access required.", "danger")
        return redirect(url_for("dashboard"))

    project = Project.query.get_or_404(project_id)
    assigned_apps = ProfessionalProjectApplication.query.filter_by(
        project_id=project.id, status="Assigned"
    ).all()
    for app in assigned_apps:
        app.status = "Applied"

    project.status = "Pending Assignment"
    db.session.commit()

    flash(f"Specialist removed from Project #{project.id}. Reset to Pending Assignment.", "success")
    return redirect(request.referrer or url_for("admin.admin_dashboard"))


@admin_bp.route("/admin/project/<int:project_id>/delete", methods=["POST"])
@login_required
def delete_project(project_id):
    if current_user.role != "admin":
        flash("Admin access required.", "danger")
        return redirect(url_for("dashboard"))

    project = Project.query.get_or_404(project_id)

    ProfessionalProjectApplication.query.filter_by(project_id=project.id).delete()
    ProjectDelivery.query.filter_by(project_id=project.id).delete()
    Payment.query.filter_by(project_id=project.id).delete()

    db.session.delete(project)
    db.session.commit()

    flash(f"Project #{project_id} has been permanently deleted.", "success")
    return redirect(request.referrer or url_for("admin.admin_dashboard"))


# =========================================================
# THE 5 PILLARS: TRANSACTIONS, BROADCASTS, REPORTS, BLOCKS
# =========================================================

@admin_bp.route("/admin/users/<int:user_id>/toggle-status", methods=["POST"])
@login_required
def toggle_user_status(user_id):
    if current_user.role != "admin":
        flash("Admin access required.", "danger")
        return redirect(url_for("dashboard"))

    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot block your own superadmin account.", "warning")
        return redirect(request.referrer or url_for("admin.admin_customers"))

    user.session_version = getattr(user, "session_version", 0) + 1
    db.session.commit()

    flash(f"User {user.email} session has been invalidated.", "success")
    return redirect(request.referrer or url_for("admin.admin_customers"))


@admin_bp.route("/admin/transactions")
@login_required
def admin_transactions():
    if current_user.role != "admin":
        flash("Admin access required.", "danger")
        return redirect(url_for("dashboard"))

    payments = Payment.query.order_by(Payment.created_at.desc()).all()
    total_collected = sum(p.amount for p in payments if p.status.lower() == "paid")
    pending_amount = sum(p.amount for p in payments if p.status.lower() in ["created", "pending"])

    return render_template(
        "admin_transactions.html",
        payments=payments,
        total_collected=total_collected,
        pending_amount=pending_amount
    )


@admin_bp.route("/admin/notifications/broadcast", methods=["POST"])
@login_required
def broadcast_notification():
    if current_user.role != "admin":
        flash("Admin access required.", "danger")
        return redirect(url_for("dashboard"))

    target_role = request.form.get("target_role", "all")
    title = request.form.get("title", "").strip()
    message = request.form.get("message", "").strip()
    link = request.form.get("link", "/dashboard").strip()

    if not title or not message:
        flash("Title and message are required for broadcasts.", "danger")
        return redirect(request.referrer or url_for("admin.admin_dashboard"))

    recipients = (
        User.query.filter(User.role != "admin").all()
        if target_role == "all"
        else User.query.filter_by(role=target_role).all()
    )

    for u in recipients:
        db.session.add(Notification(
            user_id=u.id,
            title=title,
            message=message,
            link=link
        ))

    db.session.commit()
    flash(f"Broadcast sent successfully to {len(recipients)} {target_role} recipient(s).", "success")
    return redirect(request.referrer or url_for("admin.admin_dashboard"))


# =========================================================
# PILLAR 5: COMPREHENSIVE 360° BUSINESS EXPORTS (EXCEL/CSV)
# =========================================================

@admin_bp.route("/admin/reports/export/<string:report_type>")
@login_required
def export_reports(report_type):
    if current_user.role != "admin":
        flash("Admin access required.", "danger")
        return redirect(url_for("dashboard"))

    si = StringIO()
    si.write("\ufeff")  # UTF-8 BOM for Excel rendering
    writer = csv.writer(si)

    if report_type == "revenue":
        writer.writerow([
            "Invoice #", "Payment Status", "Razorpay Payment ID", "Razorpay Order ID",
            "Payment Date (IST)", "Project ID", "Service Category", "Package Tier",
            "Customer Legal Name", "Customer Email", "Customer Phone", "Customer Business Name",
            "Customer GSTIN", "SAC Code", "Gross Invoiced (INR)", "Base Taxable Value (INR)",
            "Estimated GST (18%) (INR)", "CGST (9%) (INR)", "SGST (9%) (INR)",
            "Talent Payout Share (INR)", "Talent Payout Status", "Talent Bank UTR Ref", "Agency Net Margin (INR)"
        ])

        payments = Payment.query.order_by(Payment.created_at.desc()).all()
        for p in payments:
            project = p.project
            customer = p.customer
            profile = customer.customer_profile if customer else None
            invoice = project.invoice_record if project and hasattr(project, 'invoice_record') else None

            gross = p.amount if p.amount else 0
            base_val = round(gross / 1.18, 2) if gross > 0 else 0
            tax_val = round(gross - base_val, 2)
            cgst = round(tax_val / 2, 2)
            sgst = round(tax_val / 2, 2)
            
            talent_payout = invoice.talent_payout if invoice and hasattr(invoice, 'talent_payout') else 0
            payout_status = invoice.payout_status if invoice and hasattr(invoice, 'payout_status') else "Pending Approval"
            payout_utr = invoice.payout_utr if invoice and hasattr(invoice, 'payout_utr') else "—"
            net_profit = round(base_val - talent_payout, 2) if gross > 0 else 0

            writer.writerow([
                invoice.invoice_number if invoice and hasattr(invoice, 'invoice_number') else f"INV-2026-{p.id:04d}",
                p.status, p.razorpay_payment_id or "—", p.razorpay_order_id,
                p.created_at.strftime("%Y-%m-%d %H:%M:%S") if p.created_at else "—",
                p.project_id, project.service if project else "Direct Milestone",
                project.package if project else "Custom", customer.name if customer else "Direct Client",
                customer.email if customer else "—", profile.phone if profile and profile.phone else "—",
                profile.business_name if profile and profile.business_name else "Direct Business",
                profile.gstin if profile and hasattr(profile, 'gstin') and profile.gstin else "Unregistered",
                "998311", gross, base_val, tax_val, cgst, sgst, talent_payout, payout_status, payout_utr, net_profit
            ])
        filename = f"AgencyOS_GST_Revenue_Audit_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"

    elif report_type == "projects":
        writer.writerow([
            "Project ID", "Current Status", "Created Date (IST)", "Service Category",
            "Package Tier", "Customer Name", "Customer Email", "Customer Phone",
            "Client Business Name", "Business Type", "Business Website URL",
            "Assigned Specialist Name", "Specialist Email", "Specialist UPI ID",
            "Deliverable Submission #", "Deliverable Status", "Live Production URL",
            "Preview Staging URL", "Source Code Repository URL", "Specialist Completion Notes",
            "Revision Notes", "Project Scope & Requirements"
        ])

        projects = Project.query.order_by(Project.created_at.desc()).all()
        for prj in projects:
            customer = prj.customer
            c_profile = customer.customer_profile if customer else None
            business = prj.business

            assigned_app = ProfessionalProjectApplication.query.filter_by(
                project_id=prj.id, status="Assigned"
            ).first()
            specialist = assigned_app.professional if assigned_app else None
            s_profile = specialist.professional_profile if specialist else None

            latest_delivery = ProjectDelivery.query.filter_by(
                project_id=prj.id
            ).order_by(ProjectDelivery.submission_number.desc()).first()

            writer.writerow([
                prj.id, prj.status,
                prj.created_at.strftime("%Y-%m-%d %H:%M") if prj.created_at else "—",
                prj.service, prj.package, customer.name if customer else "Direct Client",
                customer.email if customer else "—", c_profile.phone if c_profile and c_profile.phone else "—",
                business.name if business else (c_profile.business_name if c_profile else "—"),
                business.business_type if business else "—", business.website if business else "—",
                specialist.name if specialist else "Unassigned", specialist.email if specialist else "—",
                s_profile.upi_id if s_profile and s_profile.upi_id else "Not Set",
                latest_delivery.submission_number if latest_delivery else 0,
                latest_delivery.status if latest_delivery else "Awaiting Submission",
                latest_delivery.live_url if latest_delivery and latest_delivery.live_url else "—",
                latest_delivery.preview_url if latest_delivery and latest_delivery.preview_url else "—",
                latest_delivery.source_url if latest_delivery and latest_delivery.source_url else "—",
                latest_delivery.completion_notes if latest_delivery and latest_delivery.completion_notes else "—",
                prj.revision_comment or "No active revisions",
                (prj.requirements or "").replace("\r", " ").replace("\n", " ")
            ])
        filename = f"AgencyOS_Projects_Delivery_Audit_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"

    elif report_type == "specialists":
        writer.writerow([
            "Specialist User ID", "Specialist Full Name", "Email Address", "Phone / WhatsApp",
            "Verification Status", "Core Expertise", "Skills & Technologies", "Experience Level",
            "UPI Payout ID (VPA)", "Bank Account Number", "Bank IFSC Code", "PAN Number",
            "Portfolio URL", "Total Sprints Assigned", "Completed Sprints", "Profile Score (%)", "Joined Date"
        ])

        profiles = ProfessionalProfile.query.order_by(ProfessionalProfile.created_at.desc()).all()
        for p in profiles:
            user = p.user
            assigned_count = ProfessionalProjectApplication.query.filter_by(
                professional_id=p.user_id, status="Assigned"
            ).count()
            completed_count = sum(
                1 for app in ProfessionalProjectApplication.query.filter_by(professional_id=p.user_id, status="Assigned").all()
                if app.project and app.project.status == "Completed"
            )
            score = calculate_professional_profile_completion(p)

            writer.writerow([
                p.user_id, user.name if user else "Specialist", user.email if user else "—",
                p.phone or "—", p.verification_status, p.expertise or "General",
                p.skills or "—", p.experience or "—", p.upi_id or "Not Configured",
                p.bank_account_number or "—", p.bank_ifsc or "—", p.pan_number or "—",
                p.portfolio or "—", assigned_count, completed_count, f"{score}%",
                user.created_at.strftime("%Y-%m-%d") if user and user.created_at else "—"
            ])
        filename = f"AgencyOS_Specialists_Payout_Audit_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"

    else:
        writer.writerow([
            "Customer ID", "Customer Name", "Email Address", "Phone", "Location",
            "Business Name", "Business Category", "Website", "Target Audience",
            "Business Goals", "Budget Tier", "Total Projects Ordered", "Active Sprints",
            "Completed Projects", "Total Invoiced Spend (INR)", "Profile Score (%)", "Registration Date"
        ])

        customers = User.query.filter_by(role="customer").order_by(User.created_at.desc()).all()
        for c in customers:
            profile = c.customer_profile
            business = c.businesses[0] if c.businesses else None
            all_c_projects = c.projects or []
            total_projects = len(all_c_projects)
            active_projects = sum(1 for prj in all_c_projects if prj.status in ['Assigned', 'In Progress', 'Submitted', 'Revision'])
            completed_projects = sum(1 for prj in all_c_projects if prj.status == 'Completed')
            lifetime_spend = sum(p.amount for p in c.payments if p.status and p.status.lower() == 'paid') if c.payments else 0
            
            writer.writerow([
                c.id, c.name, c.email, profile.phone if profile and profile.phone else "—",
                profile.location if profile and profile.location else "—",
                business.name if business else (profile.business_name if profile else "Direct Client"),
                business.business_type if business else (profile.business_type if profile else "—"),
                business.website if business else (profile.website if profile else "—"),
                profile.target_audience if profile and profile.target_audience else "—",
                profile.business_goals if profile and profile.business_goals else "—",
                profile.preferred_budget if profile and profile.preferred_budget else "—",
                total_projects, active_projects, completed_projects, lifetime_spend, "100%",
                c.created_at.strftime("%Y-%m-%d %H:%M") if c.created_at else "—"
            ])
        filename = f"AgencyOS_Client_CRM_Audit_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"

    output = Response(si.getvalue(), mimetype="text/csv; charset=utf-8")
    output.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return output

import json
import urllib.request
import os

# =========================================================
# INTERNAL AI COPILOT (GOOGLE GEMINI - SECURE BACKEND ROUTE)
# =========================================================

@admin_bp.route("/admin/ai/generate-sow", methods=["POST"])
@login_required
def ai_generate_sow():
    if current_user.role != "admin":
        return jsonify({"error": "Admin access required"}), 403

    client_name = request.form.get("client_name", "Valued Client").strip()
    service_type = request.form.get("service_type", "Website Design & Development").strip()
    notes = request.form.get("notes", "").strip()

    if not notes:
        return jsonify({"error": "Please provide project requirements or notes."}), 400

    api_key = os.getenv("GEMINI_API_KEY")

    # Fallback template if GEMINI_API_KEY is not yet populated in .env
    if not api_key or api_key.strip() == "":
        fallback_sow = f"""### Scope of Work: {service_type}
**Client:** {client_name}
**Project Brief:** {notes}

#### Milestone 1: Strategic Discovery & Architecture (50% Advance)
- Wireframes, information architecture, and tech stack setup.
- Deliverables: Interactive Figma prototype & project roadmap.

#### Milestone 2: Core Development & Responsive UI (25% Sign-off)
- Production coding, Razorpay payment rails, and mobile optimization.
- Deliverables: Staging URL for internal quality check.

#### Milestone 3: Production Deployment & Handover (25% Final)
- Domain DNS setup, SSL certification, and final IP transfer.
- Deliverables: Live production deployment.
"""
        return jsonify({"sow": fallback_sow})

    # Call Gemini API securely via backend
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        prompt = f"""You are an executive proposal director for a top Indian digital agency.
Draft a professional, concise 3-milestone Scope of Work (SOW) in Markdown for:
- Client: {client_name}
- Service: {service_type}
- Brief / Notes: {notes}
Structure it cleanly into:
1. Executive Summary
2. Milestone 1: Discovery & Architecture (50% Advance)
3. Milestone 2: Production Development & Testing (25% Review Gate)
4. Milestone 3: Production Handover & Deployment (25% Final)
Enforce the 2-revision limit rule. Keep it professional, crisp, and high-ticket."""

        req_data = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
        req = urllib.request.Request(url, data=req_data, headers={"Content-Type": "application/json"})
        
        with urllib.request.urlopen(req, timeout=15) as response:
            res_body = json.loads(response.read().decode("utf-8"))
            generated_text = res_body["candidates"][0]["content"]["parts"][0]["text"]
            return jsonify({"sow": generated_text})

    except Exception as e:
        return jsonify({"error": f"AI service error: {str(e)}"}), 500