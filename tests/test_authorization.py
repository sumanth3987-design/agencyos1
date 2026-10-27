"""Role-based access control tests.

Every protected page must be reachable only by the roles allowed to see it,
and every state-changing endpoint must reject callers without the right role
without mutating any data.
"""

import pytest

from app.models import (
    ProfessionalProfile,
    Project,
    Payment,
    ProfessionalProjectApplication,
)


ADMIN_PAGES = [
    "/admin/dashboard",
    "/admin/customers",
    "/admin/professionals",
    "/admin/applications",
    "/admin/project-management",
    "/admin/project-review",
]

PROFESSIONAL_PAGES = [
    "/professional/dashboard",
    "/professional/profile",
    "/professional/projects",
    "/professional/my-projects",
]

CUSTOMER_PAGES = [
    "/dashboard",
    "/customer/profile",
    "/businesses",
    "/business/add",
]

PROTECTED_PAGES = (
    CUSTOMER_PAGES
    + PROFESSIONAL_PAGES
    + ADMIN_PAGES
    + ["/payment/1", "/project/1"]
)


class TestAnonymousAccess:
    """Anonymous visitors are redirected to login for protected pages."""

    @pytest.mark.parametrize("path", PROTECTED_PAGES)
    def test_protected_pages_redirect_to_login(self, client, path):
        """Every protected page redirects anonymous visitors to /login."""

        response = client.get(path, follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]


class TestCustomerAccess:
    """Customers reach their own pages but are blocked elsewhere."""

    def test_customer_reaches_own_pages(self, client, factories, login):
        """A logged-in customer can open their own pages."""
        factories.user("customer", "cust-own@example.com")
        login("cust-own@example.com", "customer")

        for path in CUSTOMER_PAGES:
            response = client.get(path, follow_redirects=False)
            assert response.status_code == 200, path

    @pytest.mark.parametrize("path", ADMIN_PAGES)
    def test_customer_blocked_from_admin_pages(
        self, client, factories, login, path
    ):
        """Customers cannot open admin pages."""
        factories.user("customer", "cust-admin@example.com")
        login("cust-admin@example.com", "customer")

        response = client.get(path, follow_redirects=False)
        assert response.status_code == 302
        assert "/admin" not in response.headers["Location"]

    @pytest.mark.parametrize("path", PROFESSIONAL_PAGES)
    def test_customer_blocked_from_professional_pages(
        self, client, factories, login, path
    ):
        """Customers cannot open professional pages."""
        factories.user("customer", "cust-prof@example.com")
        login("cust-prof@example.com", "customer")

        response = client.get(path, follow_redirects=False)
        assert response.status_code == 302
        assert "/professional" not in response.headers["Location"]


class TestProfessionalAccess:
    """Professionals reach their own pages but are blocked elsewhere."""

    def test_professional_reaches_own_pages(self, client, factories, login):
        """A logged-in professional can open their own pages.

        /professional/profile auto-creates the profile on first visit -- this
        is the regression guard for the old NOT NULL expertise/experience
        IntegrityError (the profile must be created, not 500). The freshly
        created profile is Pending, so the verification-gated
        /professional/projects page redirects to the dashboard.
        """

        professional_id = factories.user(
            "professional", "prof-own@example.com"
        )
        login("prof-own@example.com", "professional")

        # /professional/profile bootstraps the profile (auto-create path).
        response = client.get(
            "/professional/profile", follow_redirects=False
        )
        assert response.status_code == 200

        profile = (
            ProfessionalProfile.query
            .filter_by(user_id=professional_id)
            .first()
        )
        assert profile is not None
        assert profile.expertise == ""
        assert profile.experience == ""
        assert profile.verification_status == "Pending"

        # /professional/projects is gated on verification (Pending -> redirect)
        response = client.get(
            "/professional/projects", follow_redirects=False
        )
        assert response.status_code == 302
        assert "/professional/dashboard" in response.headers["Location"]

        # /professional/dashboard and /professional/my-projects are open to
        # every logged-in professional regardless of verification status.
        for path in ("/professional/dashboard", "/professional/my-projects"):
            response = client.get(path, follow_redirects=False)
            assert response.status_code == 200, path

    @pytest.mark.parametrize("path", ADMIN_PAGES)
    def test_professional_blocked_from_admin_pages(
        self, client, factories, login, path
    ):
        """Professionals cannot open admin pages."""
        factories.user("professional", "prof-admin@example.com")
        login("prof-admin@example.com", "professional")

        response = client.get(path, follow_redirects=False)
        assert response.status_code == 302
        assert "/admin" not in response.headers["Location"]

    def test_professional_blocked_from_customer_pages(
        self, client, factories, login
    ):
        """Professionals cannot open customer pages."""
        factories.user("professional", "prof-cust@example.com")
        login("prof-cust@example.com", "professional")

        for path in CUSTOMER_PAGES:
            response = client.get(path, follow_redirects=False)
            assert response.status_code == 302, path
            assert "/dashboard" in response.headers["Location"]


class TestAdminAccess:
    """Admins reach every admin page."""

    def test_admin_reaches_admin_pages(self, client, factories, login):
        """A logged-in admin can open every admin page."""
        factories.user("admin", "admin-pages@example.com")
        login("admin-pages@example.com", "admin")

        for path in ADMIN_PAGES:
            response = client.get(path, follow_redirects=False)
            assert response.status_code == 200, path


class TestStateChangeGuards:
    """State-changing endpoints reject the wrong role without side effects.

    Each POST carries a valid CSRF token (``csrf_post``) so the request
    reaches the view's own role / ownership guard -- that is what we are
    guarding -- rather than being turned away by CSRF with a generic 400.
    CSRF rejection itself is covered by ``tests/test_csrf.py``.
    """

    def test_anonymous_state_change_redirected(self, csrf_post):
        """Anonymous POSTs to protected actions redirect to login."""

        response = csrf_post(
            "/admin/project/1/approve",
            data={},
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_non_admin_verify_professional_makes_no_change(
        self, csrf_post, factories, login
    ):
        """A non-admin cannot verify a professional."""

        professional_id = factories.user("professional", "verify-guard@example.com")
        profile_id = factories.profile(professional_id)

        factories.user("customer", "verify-actor@example.com")
        login("verify-actor@example.com", "customer")

        response = csrf_post(
            f"/admin/professionals/{profile_id}/verify",
            data={},
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert "/admin" not in response.headers["Location"]

        profile = ProfessionalProfile.query.get(profile_id)
        assert profile.verification_status == "Pending"

    def test_non_professional_apply_creates_no_application(
        self, csrf_post, factories, login
    ):
        """A customer cannot apply to a project."""

        customer_id = factories.user("customer", "apply-actor@example.com")
        project_id = factories.project(customer_id)

        login("apply-actor@example.com", "customer")

        response = csrf_post(
            f"/professional/projects/{project_id}/apply",
            data={},
            follow_redirects=False,
        )
        assert response.status_code == 302

        assert (
            ProfessionalProjectApplication.query
            .filter_by(project_id=project_id)
            .count()
            == 0
        )

    def test_non_admin_assign_creates_no_assignment(
        self, csrf_post, factories, login
    ):
        """A non-admin cannot assign a professional to a project."""

        customer_id = factories.user("customer", "assign-owner@example.com")
        project_id = factories.project(customer_id)
        professional_id = factories.user("professional", "assign-prof@example.com")
        factories.profile(professional_id, verification_status="Verified")
        application_id = factories.application(project_id, professional_id)

        factories.user("customer", "assign-actor@example.com")
        login("assign-actor@example.com", "customer")

        response = csrf_post(
            f"/admin/applications/{application_id}/assign",
            data={},
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert "/admin" not in response.headers["Location"]

        application = ProfessionalProjectApplication.query.get(application_id)
        assert application.status == "Applied"
        assert Project.query.get(project_id).status == "Pending Assignment"

    def test_non_admin_approve_makes_no_change(
        self, csrf_post, factories, login
    ):
        """A non-admin cannot approve a submitted project."""

        customer_id = factories.user("customer", "approve-owner@example.com")
        project_id = factories.project(customer_id, status="Submitted")
        professional_id = factories.user("professional", "approve-prof@example.com")
        factories.profile(professional_id, verification_status="Verified")
        factories.delivery(project_id, professional_id)

        factories.user("customer", "approve-actor@example.com")
        login("approve-actor@example.com", "customer")

        response = csrf_post(
            f"/admin/project/{project_id}/approve",
            data={},
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert "/admin" not in response.headers["Location"]

        assert Project.query.get(project_id).status == "Submitted"

    def test_customer_cannot_create_payment_order_for_other_customer(
        self, csrf_post, factories, login
    ):
        """A customer cannot create a payment order for someone else's project."""

        owner_id = factories.user("customer", "pay-owner@example.com")
        project_id = factories.project(owner_id)

        factories.user("customer", "pay-actor@example.com")
        login("pay-actor@example.com", "customer")

        response = csrf_post(
            f"/payment/create-order/{project_id}",
            data={},
            follow_redirects=False,
        )
        assert response.status_code == 404
        assert Payment.query.count() == 0
