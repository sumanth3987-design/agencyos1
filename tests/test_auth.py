from app.models import User, ProfessionalProfile

def _register(client, name="Test User", email="new@example.com",
              password="Pass123!x", account_type="customer", **extra):
    data = {
        "name": name,
        "email": email,
        "password": password,
        "account_type": account_type,
    }
    data.update(extra)
    return client.post("/register", data=data, follow_redirects=False)


class TestRegistration:

        # Customer registration
    # ---------------------------------------------------------

    def test_customer_registration_creates_user_and_profile(self, app, client):
        response = _register(client, email="cust-reg@example.com")
        assert response.status_code == 302

        with app.app_context():
            user = User.query.filter_by(
                email="cust-reg@example.com", role="customer"
            ).first()
            assert user is not None
            from werkzeug.security import check_password_hash
            assert check_password_hash(user.password, "Pass123!x")
            assert user.customer_profile is not None
            assert user.professional_profile is None

    def test_professional_registration_creates_pending_profile(self, app, client):
        response = _register(
            client,
            email="pro-reg@example.com",
            account_type="professional",
            expertise="SEO",
            experience="3 years",
        )
        assert response.status_code == 302

        with app.app_context():
            user = User.query.filter_by(
                email="pro-reg@example.com", role="professional"
            ).first()
            assert user is not None
            profile = ProfessionalProfile.query.filter_by(
                user_id=user.id
            ).first()
            assert profile is not None
            assert profile.verification_status == "Pending"

    def test_duplicate_email_same_role_rejected(self, app, client):
        with app.app_context():
            _register(client, email="dup@example.com")
            assert User.query.count() == 1

            _register(client, email="dup@example.com")
            assert User.query.count() == 1  # no second user created

    def test_same_email_other_role_allowed(self, app, client):
        # Same email as customer AND professional is allowed by design.
        _register(client, email="both@example.com", account_type="customer")
        _register(
            client, email="both@example.com", account_type="professional",
            expertise="SEO", experience="3 years",
        )
        with app.app_context():
            assert User.query.filter_by(email="both@example.com").count() == 2

    # ---------------------------------------------------------
    # Professional registration
    # ---------------------------------------------------------

    def test_professional_without_expertise_rejected(self, app, client):
        response = _register(
            client,
            email="pro-no-exp@example.com",
            account_type="professional",
        )
        assert response.status_code == 302
