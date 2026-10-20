from flask import Blueprint, jsonify
from app.models import services

api_bp = Blueprint("api", __name__)

@api_bp.route(
    "/api/services"
)
def api_services():

    return jsonify(
        services
    )


# =========================================================
# SINGLE SERVICE API
# =========================================================

@api_bp.route(
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

