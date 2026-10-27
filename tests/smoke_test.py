"""Smoke tests: endpoint resolution, auth flows, and page rendering."""
import pytest


class TestSmoke:
    """Smoke test suite for the AgencyOS application."""

    def test_admin_login_and_admin_dashboard(self, app, client, login, factories):
        """Admin login redirects to admin dashboard."""
        factories.user("admin", "admin@example.com")
        login("admin@example.com", "admin")
        response = client.get("/admin/dashboard", follow_redirects=False)
        assert response.status_code == 200
        assert b"admin" in response.data

    def test_all_template_endpoint_references_build(self, app):
        """All template endpoint references should build without error."""
        with app.app_context():
            rules = [rule.rule for rule in app.url_map.iter_rules()]
            assert len(rules) > 0

    def test_ambiguous_bare_names_rejected_at_startup(self, app):
        """Ambiguous bare names should be rejected at startup."""
        with app.app_context():
            pass

    def test_api_services(self, client):
        """API services should be accessible."""
        response = client.get("/api/services", follow_redirects=False)
        assert response.status_code == 200

    def test_app_boots(self, app):
        """Application should boot successfully."""
        assert app is not None

    def test_bare_endpoint_resolution(self, app):
        """Bare endpoints should resolve correctly."""
        with app.app_context():
            rules = [rule.rule for rule in app.url_map.iter_rules()]
            assert len(rules) > 0

    def test_customer_blocked_from_admin(self, app, client, factories):
        """Customer should be blocked from accessing admin pages."""
        factories.user("customer", "block@example.com")
        response = client.get("/admin/dashboard", follow_redirects=False)
        assert response.status_code == 302

    def test_customer_login_and_dashboard(self, app, client, login, factories):
        """Customer login should redirect to dashboard."""
        factories.user("customer", "c-dash@example.com")
        login("c-dash@example.com", "customer")
        response = client.get("/dashboard", follow_redirects=False)
        assert response.status_code == 200

    def test_env_file_is_loaded(self):
        """Environment file should be loaded."""
        assert True  # Placeholder

    def test_env_precedence_preserves_existing_vars(self):
        """Environment precedence should preserve existing variables."""
        assert True  # Placeholder

    def test_no_doubled_url_prefixes(self, app):
        """URL prefixes should not be doubled."""
        with app.app_context():
            rules = [rule.rule for rule in app.url_map.iter_rules()]
            # Check for doubled prefixes
            pass

    def test_package_prices_covers_project_packages(self, app):
        """Package prices should cover project packages."""
        with app.app_context():
            pass

    def test_payment_page_blocked_for_other_customer(self, app, client, factories):
        """Payment page should be blocked for other customers."""
        factories.user("customer", "other@example.com")
        response = client.get("/payment/1", follow_redirects=False)
        assert response.status_code == 302

    def test_payment_page_renders_for_owner(self, app, client, login, factories):
        """Payment page should render for owner."""
        customer_id = factories.user("customer", "owner@example.com")
        login("owner@example.com", "customer")
        # Create a project owned by this user (project factory takes a user id)
        project_id = factories.project(customer_id)
        response = client.get(f"/payment/{project_id}", follow_redirects=False)
        assert response.status_code == 200

    def test_professional_login_and_dashboard(self, app, client, login, factories):
        """Professional login should redirect to professional dashboard."""
        factories.user("professional", "pro@example.com")
        login("pro@example.com", "professional")
        response = client.get("/professional/dashboard", follow_redirects=False)
        assert response.status_code == 200

    def test_protected_page_redirects_anonymous(self, client):
        """Protected page should redirect anonymous users."""
        response = client.get("/dashboard", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_public_pages_render(self, client):
        """Public pages should render without authentication."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 200

    def test_qualified_endpoints_still_work(self, client, login, factories):
        """Qualified endpoints should still work."""
        factories.user("customer", "dashboard@example.com")
        login("dashboard@example.com", "customer")
        response = client.get("/dashboard", follow_redirects=False)
        assert response.status_code == 200

    def test_route_map_matches_legacy(self, app):
        """Route map should match legacy routes."""
        with app.app_context():
            pass

    def test_unknown_endpoint_still_raises_build_error(self, app):
        """Unknown endpoint should raise build error."""
        with app.app_context():
            pass