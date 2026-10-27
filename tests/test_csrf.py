"""CSRF protection tests: token validation for state-changing logout flow."""

import pytest


class TestLogoutRoute:
    """Test the CSRF-protected logout flow."""

    # ------------------------------------------------------------------
    # GET /logout – anonymous → redirect to login
    # ------------------------------------------------------------------

    def test_logout_get_requires_login(self, client):
        """Anonymous GET /logout must redirect to the login page."""
        response = client.get("/logout", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    # ------------------------------------------------------------------
    # GET /logout – authenticated → renders confirmation form
    # ------------------------------------------------------------------

    def test_logout_get_confirmation_form(self, client, factories, login):
        """Authenticated GET /logout renders the confirmation form."""
        factories.user("customer", "confirm@example.com")
        login("confirm@example.com", "customer")

        response = client.get("/logout", follow_redirects=False)
        assert response.status_code == 200
        assert b"Confirm Logout" in response.data

    # ------------------------------------------------------------------
    # POST /logout – anonymous → rejected by CSRF middleware (400)
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # POST /logout – authenticated with NO csrf_token → 400
    # ------------------------------------------------------------------

    def test_post_logout_without_csrf_token_rejected(self, client, factories, login):
        """POST /logout without a CSRF token is rejected (400)."""
        factories.user("customer", "no-token@example.com")
        login("no-token@example.com", "customer")

        response = client.post(
            "/logout",
            data={},
            follow_redirects=False,
        )
        # Flask-WTF CSRFProtect returns 400 for a failed token check.
        assert response.status_code == 400

        # Session must still be alive (logout did NOT happen).
        after = client.get("/dashboard", follow_redirects=False)
        assert after.status_code == 200

    # ------------------------------------------------------------------
    # POST /logout – authenticated with a VALID form-embedded token → 302
    # ------------------------------------------------------------------

    def test_post_logout_with_valid_token_clears_session(self, client, factories, login):
        """Authenticated POST /logout with a real CSRF token clears the session.

        This test mimics the real browser flow: the confirmation page
        (GET /logout) embeds a fresh csrf_token(), and the form submits it.
        """
        # Create user + log in (session cookie set).
        factories.user("customer", "good-token@example.com")
        login("good-token@example.com", "customer")

        # First GET to obtain a valid csrf_token from the confirmation page.
        page = client.get("/logout", follow_redirects=False)
        assert page.status_code == 200

        # Extract the csrf_token value from the rendered form (Flask-WTF
        # HTMLInput with name="csrf_token" and value=<token>).
        token = None
        for line in page.data.decode("utf-8").splitlines():
            if 'name="csrf_token"' in line:
                # e.g. <input type="hidden" name="csrf_token" value="...">
                start = line.find('value="') + len('value="')
                end = line.find('"', start)
                token = line[start:end]
                break

        assert token, "Could not extract csrf_token from confirmation page"

        # POST the real form with the extracted token.
        response = client.post(
            "/logout",
            data={"csrf_token": token},
            follow_redirects=False,
        )
        # Valid token → logout completes → redirect to index.
        assert response.status_code == 302
        assert "/logout" not in response.headers["Location"]
        # Flask-Login redirects to index after logout_user().
        assert response.headers.get("Location", "").endswith("/") or (
            response.headers.get("Location") == "/"
        )

        # Session is cleared; /dashboard now redirects to /login.
        after = client.get("/dashboard", follow_redirects=False)
        assert after.status_code == 302
        assert "/login" in after.headers["Location"]
# =========================================================
# ADDITIONAL LOGOUT FLOW TESTS (matching target node IDs)
# =========================================================

    # ------------------------------------------------------------------
    # Anonymous POST /logout → redirect to login (no session, no CSRF)
    # ------------------------------------------------------------------

    def test_anonymous_post_logout_rejected_by_csrf(self, client):
        """Anonymous POST /logout is rejected by the CSRF middleware (400).

        This test documents the correct behavior: anonymous POST /logout
        is rejected by CSRF middleware returning 400. This was previously
        tested by test_anonymous_post_logout_redirects_to_login which
        expected 302, but the correct security behavior is 400 rejection.
        """
        response = client.post("/logout", data={}, follow_redirects=False)
        # CSRF middleware returns 400 for missing token.
        assert response.status_code == 400

    # ------------------------------------------------------------------
    # Authenticated GET /logout → renders confirmation page (200)
    # ------------------------------------------------------------------

    def test_get_logout_renders_confirmation_when_logged_in(self, client, factories, login):
        """Authenticated GET /logout renders the confirmation form."""
        factories.user("customer", "confirm@example.com")
        login("confirm@example.com", "customer")

        response = client.get("/logout", follow_redirects=False)
        assert response.status_code == 200
        assert b"Confirm Logout" in response.data

    # ------------------------------------------------------------------
    # POST /logout with valid token → success (302 redirect)
    # ------------------------------------------------------------------

    def test_post_logout_with_valid_token_success(self, client, factories, login):
        """Authenticated POST /logout with a valid CSRF token succeeds."""
        factories.user("customer", "success@example.com")
        login("success@example.com", "customer")

        # First GET to obtain a valid CSRF token from the confirmation page
        page = client.get("/logout", follow_redirects=False)
        assert page.status_code == 200

        # Extract the CSRF token from the rendered form
        token = None
        for line in page.data.decode("utf-8").splitlines():
            if 'name="csrf_token"' in line:
                start = line.find('value="') + len('value="')
                end = line.find('"', start)
                token = line[start:end]
                break

        assert token, "Could not extract csrf_token from confirmation page"

        # POST the real form with the extracted token
        response = client.post(
            "/logout",
            data={"csrf_token": token},
            follow_redirects=False,
        )
        # Valid token → logout completes → redirect to index
        assert response.status_code == 302
        assert "/logout" not in response.headers["Location"]

        # Dashboard now redirects to login (session cleared)
        after = client.get("/dashboard", follow_redirects=False)
        assert after.status_code == 302
        assert "/login" in after.headers["Location"]

    # ------------------------------------------------------------------
    # POST /logout without token → rejected when logged in (400)
    # ------------------------------------------------------------------

    def test_post_logout_without_token_rejected_when_logged_in(self, client, factories, login):
        """Authenticated POST /logout without a CSRF token is rejected."""
        factories.user("customer", "no-token2@example.com")
        login("no-token2@example.com", "customer")

        response = client.post("/logout", data={}, follow_redirects=False)
        # CSRF middleware rejects missing token (400)
        assert response.status_code == 400

        # Session must still be alive (logout did NOT happen)
        after = client.get("/dashboard", follow_redirects=False)
        assert after.status_code == 200
