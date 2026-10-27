import os
import runpy
import secrets

import pytest

from app import create_app
from app.config import resolve_flask_env, validate_production_secret_key, validate_secret_key, InsecureSecretKeyError


def test_missing_env_defaults_to_production(monkeypatch):
    monkeypatch.delenv("FLASK_ENV", raising=False)
    assert resolve_flask_env() == "production"


def test_blank_env_defaults_to_production(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "   ")
    assert resolve_flask_env() == "production"


def test_environment_resolution_case_insensitive():
    assert resolve_flask_env("Development") == "development"
    assert resolve_flask_env("  PRODUCTION  ") == "production"


def test_unknown_environment_raises_value_error():
    with pytest.raises(ValueError):
        resolve_flask_env("staging")


def test_missing_secret_rejected():
    for value in (None, "", "   "):
        with pytest.raises(Exception):
            validate_production_secret_key(value)


def test_non_string_secret_rejected():
    with pytest.raises(Exception):
        validate_production_secret_key(123)


def test_known_insecure_secret_rejected():
    with pytest.raises(Exception):
        validate_production_secret_key("agencyos-development-secret-key")


def test_short_secret_rejected():
    with pytest.raises(Exception):
        validate_production_secret_key("short")


def test_weak_secret_rejected():
    with pytest.raises(Exception):
        validate_production_secret_key("a" * 40)


def test_strong_secret_accepted():
    validate_production_secret_key(secrets.token_urlsafe(32))


def test_production_debug_cannot_be_enabled_via_override():
    strong = secrets.token_urlsafe(32)
    app = create_app("production", {"SECRET_KEY": strong, "DEBUG": True})
    assert app.config["DEBUG"] is False


def test_unknown_config_name_raises_value_error():
    with pytest.raises(ValueError):
        create_app("does-not-exist")


def test_legacy_blocked_by_default(monkeypatch):
    monkeypatch.delenv("ALLOW_LEGACY_APP", raising=False)
    with pytest.raises(SystemExit):
        runpy.run_path("app_legacy.py", run_name="__main__")


def test_legacy_source_has_no_hardcoded_insecure_secret():
    source = open("app_legacy.py", encoding="utf-8", errors="replace").read()
    assert "agencyos-development-secret-key" not in source


def test_modular_app_does_not_execute_legacy():
    import sys
    sys.modules.pop("app_legacy", None)
    import app  # noqa: F401
    assert "app_legacy" not in sys.modules

def test_validate_secret_key_rejects_missing():
    for value in (None, "", "   "):
        with pytest.raises(InsecureSecretKeyError):
            validate_secret_key(value, production=False)

def test_validate_secret_key_rejects_non_string():
    with pytest.raises(InsecureSecretKeyError):
        validate_secret_key(123, production=False)

def test_validate_secret_key_rejects_short():
    with pytest.raises(InsecureSecretKeyError):
        validate_secret_key("short", production=False)

def test_validate_secret_key_accepts_strong():
    validate_secret_key(secrets.token_urlsafe(32), production=False)

def test_production_config_has_secure_cookies():
    strong = secrets.token_urlsafe(32)
    app = create_app("production", {"SECRET_KEY": strong})
    assert app.config["SESSION_COOKIE_SECURE"] is True
    assert app.config["REMEMBER_COOKIE_SECURE"] is True
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
    assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"

def test_development_config_allows_insecure_cookies():
    strong = secrets.token_urlsafe(32)
    app = create_app("development", {"SECRET_KEY": strong})
    assert app.config["SESSION_COOKIE_SECURE"] is False
    assert app.config["REMEMBER_COOKIE_SECURE"] is False
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
    assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"


def test_create_app_rejects_invalid_secret_override_development():
    for value in (None, "", "   ", 123, "short"):
        with pytest.raises(InsecureSecretKeyError):
            create_app("development", {"SECRET_KEY": value})


def test_create_app_accepts_valid_development_secret():
    strong = secrets.token_urlsafe(32)
    app = create_app("development", {"SECRET_KEY": strong})
    assert app is not None


def test_create_app_default_config_validates_secret():
    strong = secrets.token_urlsafe(32)
    app = create_app("default", {"SECRET_KEY": strong})
    assert app is not None


def test_create_app_rejects_short_default_secret():
    with pytest.raises(InsecureSecretKeyError):
        create_app("default", {"SECRET_KEY": "short"})


def test_create_app_production_rejects_insecure_fallback():
    with pytest.raises(InsecureSecretKeyError):
        create_app("production", {"SECRET_KEY": "agencyos-development-secret-key"})


def test_create_app_production_accepts_strong_secret():
    strong = secrets.token_urlsafe(32)
    app = create_app("production", {"SECRET_KEY": strong})
    assert app is not None
