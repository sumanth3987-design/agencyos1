import os
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

# Load repository .env before Config reads os.getenv.
# - Anchored to the project root so it works from any working directory.
# - load_dotenv does NOT override variables already set in the
#   environment, preserving standard env-var precedence.
# - Loads silently; no values are printed anywhere in this module.
load_dotenv(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        ".env",
    )
)


def resolve_flask_env(env=None):
    """Resolve the Flask environment name in a safe, centralized way.

    Missing or blank values resolve to ``"production"`` so that an unset
    ``FLASK_ENV`` can never accidentally enable development/debug mode.
    Unknown values raise ``ValueError`` instead of being coerced.
    """
    if env is None:
        env = os.getenv("FLASK_ENV")

    if env is None or str(env).strip() == "":
        return "production"

    value = str(env).strip().lower()
    if value == "development":
        return "development"
    if value == "production":
        return "production"

    raise ValueError(
        "Unknown FLASK_ENV value: %r. Expected 'development' or 'production'."
        % env
    )


_INSECURE_FALLBACKS = {
    "agencyos-development-secret-key",
    "agencyos-secure-fallback-key-change-in-prod",
    "placeholder_secret",
}


class InsecureSecretKeyError(ValueError, RuntimeError):
    """Raised when a production secret key is missing or insecure."""


def validate_secret_key(secret_key, production=False):
    """Validate SECRET_KEY for any environment.

    When ``production`` is True, applies full production-strength validation:
    rejects known insecure fallbacks and requires at least 8 unique
    characters. Otherwise, requires a non-empty string of at least 32
    characters.
    """
    if not isinstance(secret_key, str):
        raise InsecureSecretKeyError(
            "SECRET_KEY must be a non-empty string of at least 32 characters."
        )

    if secret_key.strip() == "":
        raise InsecureSecretKeyError(
            "SECRET_KEY is required but was not set in the environment."
        )

    if len(secret_key) < 32:
        raise InsecureSecretKeyError(
            "SECRET_KEY is too short; it must be at least 32 characters long."
        )

    if production:
        if secret_key in _INSECURE_FALLBACKS:
            raise InsecureSecretKeyError(
                "SECRET_KEY is set to a known insecure fallback value. "
                "Set a strong, unique SECRET_KEY in the environment."
            )
        if len(set(secret_key)) < 8:
            raise InsecureSecretKeyError(
                "SECRET_KEY is too weak; use a cryptographically random value."
            )


def validate_production_secret_key(secret_key):
    """Raise if the secret key is missing or insecure for production."""
    validate_secret_key(secret_key, production=True)


class InsecureRazorpayCredentialsError(ValueError, RuntimeError):
    """Raised when production Razorpay credentials are missing or placeholders."""


def validate_production_razorpay_credentials(*args, **kwargs):
    """Raise if Razorpay credentials are missing or placeholders in production.

    Accepts either two positional values ``(key_id, key_secret)`` or a
    mapping/object containing ``RAZORPAY_KEY_ID`` and
    ``RAZORPAY_KEY_SECRET``.
    """
    key_id = kwargs.get("key_id", kwargs.get("razorpay_key_id"))
    key_secret = kwargs.get("key_secret", kwargs.get("razorpay_key_secret"))

    if key_id is None and key_secret is None and args:
        if len(args) == 1 and isinstance(args[0], dict):
            config = args[0]
            key_id = config.get("RAZORPAY_KEY_ID", config.get("razorpay_key_id"))
            key_secret = config.get(
                "RAZORPAY_KEY_SECRET", config.get("razorpay_key_secret")
            )
        elif len(args) == 1 and hasattr(args[0], "get"):
            config = args[0]
            key_id = config.get("RAZORPAY_KEY_ID", config.get("razorpay_key_id"))
            key_secret = config.get(
                "RAZORPAY_KEY_SECRET", config.get("razorpay_key_secret")
            )
        elif len(args) >= 2:
            key_id = args[0]
            key_secret = args[1]

    if not isinstance(key_id, str) or key_id.strip() == "":
        raise InsecureRazorpayCredentialsError(
            "RAZORPAY_KEY_ID is required in production."
        )
    if not isinstance(key_secret, str) or key_secret.strip() == "":
        raise InsecureRazorpayCredentialsError(
            "RAZORPAY_KEY_SECRET is required in production."
        )
    if key_id.strip() == "rzp_test_placeholder":
        raise InsecureRazorpayCredentialsError(
            "RAZORPAY_KEY_ID is set to a placeholder value. "
            "Configure a real Razorpay key ID."
        )
    if key_secret.strip() == "placeholder_secret":
        raise InsecureRazorpayCredentialsError(
            "RAZORPAY_KEY_SECRET is set to a placeholder value. "
            "Configure a real Razorpay key secret."
        )


# Backwards/alternative names for compatibility with callers and tests.
validate_razorpay_credentials = validate_production_razorpay_credentials
validate_production_razorpay_config = validate_production_razorpay_credentials
validate_razorpay_config = validate_production_razorpay_credentials



class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///agencyos.db")
    if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Secure session/remember-me cookies.
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"

    # Razorpay Integration
    RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "rzp_test_placeholder")
    RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "placeholder_secret")

    # Timezone
    IST = ZoneInfo("Asia/Kolkata")


class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


# Prevent silent application startup with a missing or insecure SECRET_KEY.
# load_dotenv() above has already loaded environment variables from .env.
# This validates the default (development) configuration; production
# validation is performed in create_app() via validate_production_secret_key.
validate_secret_key(os.getenv("SECRET_KEY"), production=False)
