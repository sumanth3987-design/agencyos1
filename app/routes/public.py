from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.extensions import db, csrf
from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
public_bp = Blueprint("public", __name__)

@public_bp.route("/privacy")
def privacy():
    return render_template("legal/privacy.html")

@public_bp.route("/terms")
def terms():
    return render_template("legal/terms.html")

@public_bp.route("/refund-policy")
def refund_policy():
    return render_template("legal/refund.html")

@public_bp.route("/contact")
def contact():
    return render_template("legal/contact.html")

@public_bp.route("/api/free-audit", methods=["POST"])
@csrf.exempt
def free_audit():
    business_url = request.form.get("business_url", "").strip()

    if not business_url:
        flash("Please enter a valid website URL or business name.", "error")
        return redirect(url_for("auth.index") + "#audit")

    # In a full flow, this saves to a Lead table or triggers a WhatsApp ping
    flash("Audit requested successfully! Our team is analyzing your site and will WhatsApp you within 60 minutes.", "success")
    return redirect(url_for("auth.index") + "#audit")
