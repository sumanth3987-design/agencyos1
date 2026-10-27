"""Focused regression tests for test-database URL validation."""

import pytest

from tests.conftest import (
    _configured_test_database_url,
    _postgresql_connection_identity,
    _validate_test_database_url,
)


def test_postgresql_connection_identity_normalizes_spellings_and_default_port():
    expected = ("localhost", 5432, "agencyos_test")

    assert _postgresql_connection_identity(
        "postgres://user:secret@localhost/agencyos_test"
    ) == expected
    assert _postgresql_connection_identity(
        "postgresql://user:secret@localhost:5432/agencyos_test"
    ) == expected
    assert _postgresql_connection_identity(
        "postgresql+psycopg://user:secret@localhost/agencyos_test"
    ) == expected
    assert _postgresql_connection_identity(
        "postgresql+psycopg2://user:secret@LOCALHOST:5432/agencyos_test"
    ) == ("localhost", 5432, "agencyos_test")


def test_postgresql_connection_identity_returns_none_for_non_postgresql_urls():
    assert _postgresql_connection_identity("sqlite:///tmp.db") is None
    assert _postgresql_connection_identity("mysql://user:secret@localhost/db_test") is None
    assert _postgresql_connection_identity("not-a-url") is None


@pytest.mark.parametrize(
    "raw_url",
    [
        "postgresql://user:secret@localhost:5432/agencyos_test",
        "postgresql+psycopg://user:secret@localhost/agencyos_test",
    ],
)
def test_validate_accepts_dedicated_postgresql_spellings(raw_url, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    result = _validate_test_database_url(raw_url)

    assert result.startswith("postgresql+psycopg://")
    assert result.endswith("/agencyos_test")


def test_validate_rejects_non_dedicated_database_name(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(ValueError, match="dedicated test database"):
        _validate_test_database_url("postgresql://user:secret@localhost/agencyos")


def test_validate_rejects_unsupported_driver(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(ValueError, match="approved PostgreSQL driver"):
        _validate_test_database_url("mysql://user:secret@localhost/agencyos_test")


def test_validate_rejects_application_database_with_equivalent_spellings(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgres://user:secret@db.example.com:5432/shared_test",
    )

    with pytest.raises(ValueError, match="must not target the application database"):
        _validate_test_database_url(
            "postgresql://user:secret@DB.example.com/shared_test"
        )


def test_validate_allows_dedicated_test_database_when_application_differs(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:secret@localhost:5432/appdb")

    result = _validate_test_database_url(
        "postgresql://user:secret@localhost:5432/agencyos_test"
    )

    assert result.startswith("postgresql+psycopg://")
    assert result.endswith("/agencyos_test")


def test_configured_test_database_url_defaults_to_empty(monkeypatch):
    monkeypatch.delenv("TEST_DATABASE_URL", raising=False)

    assert _configured_test_database_url() == ""
