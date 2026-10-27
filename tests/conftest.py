"""Common pytest fixtures for the AgencyOS test suite."""

import os

import pytest
from sqlalchemy.engine.url import make_url

from app import create_app
from app.extensions import db as _db


def _is_postgresql_driver(drivername):
    """Return whether a SQLAlchemy driver name refers to PostgreSQL."""
    normalized = (drivername or "").strip().lower()
    return normalized == "postgres" or normalized.startswith("postgresql")


def _postgresql_connection_identity(raw_url):
    """Return a credential-free identity for a PostgreSQL connection.

    Equivalent spellings such as ``postgres://``, ``postgresql://``, and
    ``postgresql+psycopg://`` are normalized to the same identity.  Omitted
    ports default to PostgreSQL's standard port.  Credentials, driver spelling,
    and query options are deliberately excluded.  ``None`` is returned for
    non-PostgreSQL or unparseable URLs.
    """
    try:
        url = make_url(raw_url)
    except Exception:
        return None

    if not _is_postgresql_driver(url.drivername):
        return None

    host = (url.host or "").strip().lower()
    port = url.port
    if port is None:
        port = 5432
    database = url.database or ""
    return (host, port, database)


def _configured_test_database_url():
    """Return the explicitly configured PostgreSQL test database URL, if any."""
    return os.getenv("TEST_DATABASE_URL", "").strip()


def _validate_test_database_url(raw_url):
    """Validate and normalize an opt-in PostgreSQL test database URL.

    The URL is never logged. Validation fails closed: an invalid, shared,
    or non-dedicated database URL raises instead of falling back to SQLite.
    """
    try:
        url = make_url(raw_url)
    except Exception as exc:
        raise ValueError("TEST_DATABASE_URL is not a valid SQLAlchemy URL.") from exc

    # Normalize the canonical PostgreSQL driver spelling to the single
    # approved driver. Other PostgreSQL drivers are rejected.
    if url.drivername == "postgresql":
        url = url.set(drivername="postgresql+psycopg")
    if url.drivername != "postgresql+psycopg":
        raise ValueError(
            "TEST_DATABASE_URL must use the approved PostgreSQL driver "
            "(postgresql+psycopg)."
        )

    database_name = url.database or ""
    if not (
        database_name.endswith("_test") or database_name.endswith("_ci")
    ):
        raise ValueError(
            "TEST_DATABASE_URL must target a dedicated test database whose "
            "name ends in '_test' or '_ci'."
        )

    # Prevent accidental use of the application/development database, including
    # equivalent PostgreSQL spellings and omitted default ports.
    application_url = os.getenv("DATABASE_URL", "").strip()
    if application_url:
        application_identity = _postgresql_connection_identity(application_url)
        test_identity = _postgresql_connection_identity(url)
        if (
            application_identity is not None
            and test_identity is not None
            and application_identity == test_identity
        ):
            raise ValueError(
                "TEST_DATABASE_URL must not target the application database."
            )

    return url.render_as_string(hide_password=False)


def extract_csrf_token(html_text):
    """Pull the first embedded ``csrf_token`` value out of rendered HTML."""
    token = None

    for line in html_text.splitlines():
        if 'name="csrf_token"' in line:
            start = line.find('value="') + len('value="')
            end = line.find('"', start)
            token = line[start:end]
            break

    return token


def assert_test_database(application):
    """Fail closed before schema operations, checking engines rather than config."""
    assert application.config["TESTING"] is True
    assert application.config["WTF_CSRF_ENABLED"] is True
    assert set(_db.engines) == {None}, "Unexpected database binds in tests"
    for engine in _db.engines.values():
        url = engine.url
        if url.drivername == "sqlite":
            assert url.database == ":memory:", "Refusing a non-memory database"
        elif url.drivername.startswith("postgresql+psycopg"):
            database_name = url.database or ""
            assert (
                database_name.endswith("_test")
                or database_name.endswith("_ci")
            ), "Refusing a non-test PostgreSQL database"
        else:
            raise AssertionError(
                "Unsupported test database driver: %s" % url.drivername
            )


@pytest.fixture
def app():
    """Configure the isolated engine before initializing SQLAlchemy."""
    raw_test_database_url = _configured_test_database_url()
    if raw_test_database_url:
        sqlalchemy_database_uri = _validate_test_database_url(
            raw_test_database_url
        )
        sqlalchemy_engine_options = {"pool_pre_ping": True}
    else:
        sqlalchemy_database_uri = "sqlite:///:memory:"
        sqlalchemy_engine_options = {}

    try:
        app = create_app("default", {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": sqlalchemy_database_uri,
            "SQLALCHEMY_BINDS": {},
            "SQLALCHEMY_ENGINE_OPTIONS": sqlalchemy_engine_options,
            "WTF_CSRF_ENABLED": True,
            "SECRET_KEY": "test-secret-key-0123456789abcdef0123456789abcdef",
        })
    except Exception as exc:
        # Fail closed: do not silently fall back to another database.
        raise RuntimeError(
            "Unable to initialize the configured test database: %s"
            % type(exc).__name__
        ) from exc

    with app.app_context():
        try:
            assert_test_database(app)
            _db.create_all()
        except Exception as exc:
            raise RuntimeError(
                "Unable to initialize the configured test database: %s"
                % type(exc).__name__
            ) from exc
        try:
            yield app
        finally:
            _db.session.remove()
            assert_test_database(app)
            _db.drop_all()
            _db.engine.dispose()


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture
def db(app):
    """Provide the database instance."""
    return _db


@pytest.fixture
def factories(app):
    """Provide factory helpers for creating test data."""
    from app.models import (
        User,
        CustomerProfile,
        ProfessionalProfile,
        Project,
        Payment,
        ProfessionalProjectApplication,
        ProjectDelivery,
    )
    from werkzeug.security import generate_password_hash

    DEFAULT_PASSWORD = "TestPass123!"

    class _Factories:
        def user(self, role, email, **kwargs):
            """Create a user with the given role."""
            # ``password_hash`` is accepted as an alias for a raw password
            # so that factories stay usable regardless of which spelling a
            # test uses.
            password = kwargs.pop(
                "password",
                kwargs.pop("password_hash", DEFAULT_PASSWORD)
            )
            kwargs.setdefault("name", email.split("@")[0])

            user = User(
                email=email,
                password=generate_password_hash(password),
                role=role,
                **kwargs
            )
            _db.session.add(user)
            _db.session.commit()
            return user.id

        def customer(self, email, **kwargs):
            return self.user("customer", email, **kwargs)

        def professional(self, email, **kwargs):
            return self.user("professional", email, **kwargs)

        def admin(self, email, **kwargs):
            return self.user("admin", email, **kwargs)

        def customer_profile(self, user_id, **kwargs):
            """Create a customer profile."""
            profile = CustomerProfile(user_id=user_id, **kwargs)
            _db.session.add(profile)
            _db.session.commit()
            return profile.id

        def profile(self, user_id, **kwargs):
            """Create a professional profile (defaults to Pending)."""
            kwargs.setdefault("expertise", "Website Design & Development")
            kwargs.setdefault("experience", "3 years")
            kwargs.setdefault("verification_status", "Pending")
            profile = ProfessionalProfile(user_id=user_id, **kwargs)
            _db.session.add(profile)
            _db.session.commit()
            return profile.id

        def project(self, customer_id, **kwargs):
            """Create a project owned by the customer."""
            kwargs.setdefault("service", "Website Design & Development")
            kwargs.setdefault("package", "Basic Website")
            kwargs.setdefault("requirements", "Build a website")
            kwargs.setdefault("status", "Pending Assignment")
            project = Project(customer_id=customer_id, **kwargs)
            _db.session.add(project)
            _db.session.commit()
            return project.id

        def application(self, project_id, professional_id, **kwargs):
            """Create a project application."""
            kwargs.setdefault("status", "Applied")
            application = ProfessionalProjectApplication(
                project_id=project_id,
                professional_id=professional_id,
                **kwargs
            )
            _db.session.add(application)
            _db.session.commit()
            return application.id

        def delivery(self, project_id, professional_id, **kwargs):
            """Create a delivery record."""
            kwargs.setdefault("submission_number", 1)
            kwargs.setdefault("completion_notes", "Work completed")
            kwargs.setdefault("status", "Submitted")
            delivery = ProjectDelivery(
                project_id=project_id,
                professional_id=professional_id,
                **kwargs
            )
            _db.session.add(delivery)
            _db.session.commit()
            return delivery.id

        def payment(self, project_id, customer_id, **kwargs):
            """Create a payment row."""
            kwargs.setdefault("razorpay_order_id", "order_test_1")
            kwargs.setdefault("amount", 4999)
            kwargs.setdefault("currency", "INR")
            kwargs.setdefault("status", "Created")
            payment = Payment(
                project_id=project_id,
                customer_id=customer_id,
                **kwargs
            )
            _db.session.add(payment)
            _db.session.commit()
            return payment.id

    return _Factories()


@pytest.fixture
def login(client, app, csrf_token):
    """Log in a user and return the login response."""
    def _login(email, role, password="TestPass123!"):
        return client.post(
            "/login",
            data={
                "email": email,
                "password": password,
                "login_role": role,
                "csrf_token": csrf_token,
            },
            follow_redirects=True,  # Follow redirect to maintain session
        )
    return _login


@pytest.fixture
def csrf_token(client, app):
    """Return a valid CSRF token bound to the current test session.

    Flask-WTF keeps a random *raw* value in ``session['csrf_token']`` and
    sends the client a signed version of it. Both halves are produced here
    so POST helpers never have to scrape a rendered template.
    """
    import hashlib
    import os

    from itsdangerous import URLSafeTimedSerializer

    raw_token = hashlib.sha1(os.urandom(64)).hexdigest()

    secret_key = (
        app.config.get("WTF_CSRF_SECRET_KEY")
        or app.config["SECRET_KEY"]
    )

    signed_token = URLSafeTimedSerializer(
        secret_key,
        salt="wtf-csrf-token",
    ).dumps(raw_token)

    with client.session_transaction() as session:
        session["csrf_token"] = raw_token

    return signed_token


@pytest.fixture
def csrf_post(client, csrf_token):
    """POST helper that always submits a valid CSRF token."""
    def _post(url, data=None, **kwargs):
        payload = dict(data or {})
        payload["csrf_token"] = csrf_token
        return client.post(url, data=payload, **kwargs)
    return _post
def pytest_configure(config):
    """Register the opt-in PostgreSQL test marker."""
    config.addinivalue_line(
        "markers",
        "postgres: requires TEST_DATABASE_URL pointing to a dedicated "
        "PostgreSQL test database",
    )
