import os
from flask import Flask, url_for
from werkzeug.routing import BuildError
from app.config import (
    config_by_name,
    validate_production_secret_key,
    validate_production_razorpay_credentials,
)
from app.extensions import db, login_manager, csrf


def _build_bare_endpoint_map(view_functions):
    """Map bare endpoint names to qualified blueprint endpoints.

    Templates and blueprint code call url_for("dashboard") in the style
    of the legacy monolithic app.py, while blueprint endpoints are
    qualified (e.g. "customer.dashboard"). A bare name that resolves to
    more than one blueprint function would be ambiguous and is rejected
    at startup. App-level endpoints such as "static" are already bare
    and are skipped.
    """

    bare_map = {}
    ambiguous = set()

    for endpoint in view_functions:

        if "." not in endpoint:
            continue

        bare = endpoint.split(".", 1)[1]

        if bare in bare_map and bare_map[bare] != endpoint:
            ambiguous.add(bare)

        bare_map[bare] = endpoint

    if ambiguous:
        raise RuntimeError(
            "Ambiguous bare endpoint names across blueprints: "
            + ", ".join(sorted(ambiguous))
        )

    return bare_map


def create_app(config_name="default", config_overrides=None):
    if config_name not in config_by_name:
        raise ValueError(
            "Unknown configuration name: %r. "
            "Expected one of: %s."
            % (config_name, ", ".join(sorted(config_by_name)))
        )

    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object(config_by_name[config_name])
    if config_overrides is not None:
        app.config.update(config_overrides)

    # Production is always non-debug, even if an override tries to enable it.
    if config_name == "production":
        app.config["DEBUG"] = False
        # Fail safely in production when the secret is missing or insecure.
        # Validated after overrides are applied.
        validate_production_secret_key(app.config.get("SECRET_KEY"))
        # Fail safely in production when Razorpay credentials are missing
        # or still set to development placeholders.
        validate_production_razorpay_credentials(
            app.config.get("RAZORPAY_KEY_ID"),
            app.config.get("RAZORPAY_KEY_SECRET"),
        )

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Blueprints
    from app.blueprints.auth import auth_bp
    from app.blueprints.customer import customer_bp
    from app.blueprints.professional import professional_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.payments import payments_bp
    from app.blueprints.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(professional_bp)
    # Route rules in these blueprints already carry their full paths
    # (/admin/..., /payment/..., /api/...), so no url_prefix here.
    app.register_blueprint(admin_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(api_bp)

    # ------------------------------------------------------------
    # Legacy bare-endpoint resolver
    # ------------------------------------------------------------
    # url_for("dashboard")-style calls must resolve to the single
    # qualified blueprint endpoint. Unknown endpoints re-raise the
    # original BuildError unchanged.
    bare_map = _build_bare_endpoint_map(app.view_functions)

    def resolve_bare_endpoint(error, endpoint, values):

        if "." in endpoint:
            return None

        qualified = bare_map.get(endpoint)

        if not qualified:
            return None

        try:
            return url_for(qualified, **values)
        except BuildError:
            return None

    app.url_build_error_handlers.append(resolve_bare_endpoint)

    return app
