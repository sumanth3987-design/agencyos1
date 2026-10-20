from functools import wraps
from flask import flash, redirect, url_for, abort, jsonify, request
from flask_login import current_user

def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.login"))
            if current_user.role not in allowed_roles:
                if request.is_json:
                    return jsonify({"error": "Unauthorized access", "required_roles": allowed_roles}), 403
                flash("You do not have permission to view this page.", "danger")
                return redirect(url_for("customer.dashboard"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def verified_professional_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        profile = getattr(current_user, "professional_profile", None)
        if not profile or getattr(profile, "verification_status", "Pending") != "Verified":
            flash("Your profile must be verified by an administrator before accessing project applications.", "warning")
            return redirect(url_for("professional.dashboard"))
        return f(*args, **kwargs)
    return decorated_function
