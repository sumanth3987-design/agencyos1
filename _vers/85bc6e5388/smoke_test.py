"""
Non-destructive smoke tests for AgencyOS Stage 1 (startup restoration).

Runs exclusively against an in-memory SQLite database. The real
instance/agencyos.db file is never opened by this suite: DATABASE_URL
is forced to sqlite:///:memory: BEFORE the app package is imported.

Run:  venv\\Scripts\\python.exe tests\\smoke_test.py
"""

import os
import re
import sys
import glob
import subprocess
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

# Force in-memory DB before any app import (must come first).
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from werkzeug.security import generate_password_hash  # noqa: E402
from werkzeug.routing import BuildError  # noqa: E402

from app import create_app, _build_bare_endpoint_map  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import (  # noqa: E402
    User, CustomerProfile, Project, PACKAGE_PRICES
)

SECRET_KEY_FALLBACK = "agencyos-secure-fallback-key-change-in-prod"

# Exact route paths of the working legacy monolithic app.py (39 routes).
LEGACY_ROUTES = {
    "/",
    "/admin/applications",
    "/admin/applications/<int:application_id>/assign",
    "/admin/customers",
    "/admin/dashboard",
    "/admin/professionals",
    "/admin/professionals/<int:profile_id>/reject",
    "/admin/professionals/<int:profile_id>/verify",
    "/admin/project-management",
    "/admin/project-review",
    "/admin/project/<int:project_id>/approve",
    "/admin/project/<int:project_id>/revision",
    "/api/service/<slug>",
    "/api/services",
    "/business/<int:business_id>",
    "/business/<int:business_id>/delete",
    "/business/<int:business_id>/edit",
    "/business/add",
    "/businesses",
    "/customer/profile",
    "/dashboard",
    "/login",
    "/logout",
    "/payment/<int:project_id>",
    "/payment/create-order/<int:project_id>",
    "/payment/verify",
    "/professional/dashboard",
    "/professional/my-projects",
    "/professional/profile",
    "/professional/project/<int:project_id>",
    "/professional/project/<int:project_id>/resubmit",
    "/professional/project/<int:project_id>/start",
    "/professional/project/<int:project_id>/submit",
    "/professional/projects",
    "/professional/projects/<int:project_id>/apply",
    "/project/<int:project_id>",
    "/register",
    "/requirements/<service_slug>",
    "/start-project/<service_slug>",
}

SAMPLE_VALUES = {
    "project_id": 1,
    "business_id": 1,
    "application_id": 1,
    "profile_id": 1,
    "service_slug": "website-development",
    "filename": "app.css",
}

def template_url_for_names():
    """Collect every endpoint name referenced by url_for in templates."""
    pattern = re.compile(r"url_for\(\s*['\"]([^'\"]+)")
    names = set()
    for path in glob.glob(os.path.join(BASE_DIR, "templates", "*.html")):
        with open(path, encoding="utf-8", errors="replace") as fh:
            names.update(pattern.findall(fh.read()))
    return names

class SmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app("development")
        cls.app.config["TESTING"] = True
        with cls.app.app_context():
            db.create_all()
            customer = User(
                name="Smoke Customer",
                email="smoke-customer@example.com",
                password=generate_password_hash("SmokePass123!"),
                role="customer",
            )
            db.session.add(customer)
            db.session.flush()
            db.session.add(CustomerProfile(user_id=customer.id))
            professional = User(
                name="Smoke Pro",
                email="smoke-pro@example.com",
                password=generate_password_hash("SmokePass123!"),
                role="professional",
            )
            admin = User(
                name="Smoke Admin",
                email="smoke-admin@example.com",
                password=generate_password_hash("SmokePass123!"),
                role="admin",
            )
            db.session.add_all([professional, admin])
            db.session.flush()
            project = Project(
                customer_id=customer.id,
                service="Website Design & Development",
                package="Basic Website",
                requirements="Smoke test project",
                status="Draft",
            )
            db.session.add(project)
            db.session.commit()
            cls.customer_id = customer.id
            cls.admin_id = admin.id
            cls.project_id = project.id
        cls.client = cls.app.test_client()

    # --------------------------------------------------------
    # Startup / route registration
    # --------------------------------------------------------

    def test_app_boots(self):
        self.assertIsNotNone(self.app)

    def test_route_map_matches_legacy(self):
        rules = {str(r) for r in self.app.url_map.iter_rules()}
        missing = LEGACY_ROUTES - rules
        self.assertFalse(missing, f"Missing legacy routes: {sorted(missing)}")

    def test_no_doubled_url_prefixes(self):
        rules = {str(r) for r in self.app.url_map.iter_rules()}
        doubled = [
            r for r in rules
            if r.startswith(("/admin/admin", "/api/api", "/payment/payment"))
        ]
        self.assertEqual(doubled, [], f"Doubled prefixes present: {doubled}")

    # --------------------------------------------------------
    # URL generation
    # --------------------------------------------------------

    def test_bare_endpoint_resolution(self):
        with self.app.test_request_context():
            from flask import url_for
            self.assertEqual(url_for("dashboard"), "/dashboard")
            self.assertEqual(url_for("index"), "/")
            self.assertEqual(url_for("login"), "/login")
            self.assertEqual(url_for("logout"), "/logout")
            self.assertEqual(url_for("register"), "/register")
            self.assertEqual(url_for("admin_dashboard"), "/admin/dashboard")
            self.assertEqual(url_for("api_services"), "/api/services")
            self.assertEqual(
                url_for("payment_page", project_id=1), "/payment/1"
            )
            self.assertEqual(url_for("verify_payment"), "/payment/verify")

    def test_qualified_endpoints_still_work(self):
        with self.app.test_request_context():
            from flask import url_for
            self.assertEqual(url_for("customer.dashboard"), "/dashboard")
            self.assertEqual(url_for("auth.index"), "/")
            self.assertEqual(
                url_for("admin.admin_dashboard"), "/admin/dashboard"
            )

    def test_all_template_endpoint_references_build(self):
        unresolved = []
        with self.app.test_request_context():
            from flask import url_for
            for name in sorted(template_url_for_names()):
                try:
                    url_for(name, **SAMPLE_VALUES)
                except BuildError:
                    unresolved.append(name)
        self.assertEqual(
            unresolved, [],
            f"Template url_for endpoints that fail to build: {unresolved}"
        )

    def test_unknown_endpoint_still_raises_build_error(self):
        with self.app.test_request_context():
            from flask import url_for
            with self.assertRaises(BuildError):
                url_for("no_such_endpoint_anywhere")

    def test_ambiguous_bare_names_rejected_at_startup(self):
        def _a(): pass
        def _b(): pass
        with self.assertRaises(RuntimeError) as ctx:
            _build_bare_endpoint_map({"one.foo": _a, "two.foo": _b})
        self.assertIn("foo", str(ctx.exception))

    # --------------------------------------------------------
    # .env loading & precedence (subprocess; no secrets printed)
    # --------------------------------------------------------

    def _run_env_check(self, extra_env):
        env = os.environ.copy()
        env["DATABASE_URL"] = "sqlite:///:memory:"
        env.update(extra_env)
        script = (
            "import os, sys\n"
            f"sys.path.insert(0, {BASE_DIR!r})\n"
            "import app.config  # triggers load_dotenv\n"
            "checks = []\n"
            "checks.append(('SECRET_KEY_LOADED',"
            " bool(os.environ.get('SECRET_KEY')) and"
            f" os.environ['SECRET_KEY'] != {SECRET_KEY_FALLBACK!r}))\n"
            "checks.append(('RAZORPAY_KEY_ID_LOADED',"
            " bool(os.environ.get('RAZORPAY_KEY_ID'))))\n"
            "if 'EXPECTED_SECRET_KEY' in os.environ:\n"
            "    checks.append(('PRESERVED_PRESET_SECRET_KEY',"
            " os.environ.get('SECRET_KEY')"
            " == os.environ['EXPECTED_SECRET_KEY']))\n"
            "print(','.join(f'{k}={int(v)}' for k, v in checks))\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True, text=True, env=env,
            cwd=BASE_DIR, timeout=120,
        )
        self.assertEqual(
            result.returncode, 0,
            f"subprocess failed: {result.stderr[-500:]}",
        )
        return result.stdout.strip().splitlines()[-1]

    def test_env_file_is_loaded(self):
        # Without a pre-set SECRET_KEY, .env values must take effect and
        # the insecure fallback must NOT be used.
        out = self._run_env_check({})
        self.assertIn("SECRET_KEY_LOADED=1", out)
        self.assertIn("RAZORPAY_KEY_ID_LOADED=1", out)

    def test_env_precedence_preserves_existing_vars(self):
        # A SECRET_KEY already in the environment must NOT be
        # overridden by .env (dotenv default behavior).
        out = self._run_env_check(
            {
                "SECRET_KEY": "precedence-test-value",
                "EXPECTED_SECRET_KEY": "precedence-test-value",
            }
        )
        self.assertIn("PRESERVED_PRESET_SECRET_KEY=1", out)


    def test_real_app_bare_map_has_no_ambiguity(self):
        # create_app() succeeded in setUpClass, which already proves the
        # real endpoint set is unambiguous; re-check the helper directly.
        _build_bare_endpoint_map(self.app.view_functions)

    # --------------------------------------------------------
    # Page smoke tests (auth behavior unchanged)
    # --------------------------------------------------------

    def _login(self, email, role):
        return self.client.post(
            "/login",
            data={
                "email": email,
                "password": "SmokePass123!",
                "login_role": role,
            },
            follow_redirects=False,
        )

    def test_public_pages_render(self):
        for path in ("/", "/login", "/register"):
            response = self.client.get(path)
            self.assertEqual(
                response.status_code, 200, f"{path} -> {response.status_code}"
            )

    def test_protected_page_redirects_anonymous(self):
        # Fresh client so no login session from another test leaks in.
        anon = self.app.test_client()
        response = anon.get("/dashboard", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

    def test_customer_login_and_dashboard(self):
        response = self._login("smoke-customer@example.com", "customer")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/dashboard")
        for path in ("/dashboard", "/businesses", "/customer/profile"):
            page = self.client.get(path)
            self.assertEqual(
                page.status_code, 200, f"{path} -> {response.status_code}"
            )

    def test_customer_blocked_from_admin(self):
        self._login("smoke-customer@example.com", "customer")
        response = self.client.get("/admin/dashboard", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/dashboard")

    def test_admin_login_and_admin_dashboard(self):
        response = self._login("smoke-admin@example.com", "admin")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/admin/dashboard")
        page = self.client.get("/admin/dashboard")
        self.assertEqual(page.status_code, 200)

    def test_professional_login_and_dashboard(self):
        response = self._login("smoke-pro@example.com", "professional")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.headers["Location"], "/professional/dashboard"
        )
        page = self.client.get("/professional/dashboard")
        self.assertEqual(page.status_code, 200)

    def test_payment_page_renders_for_owner(self):
        self._login("smoke-customer@example.com", "customer")
        page = self.client.get(f"/payment/{self.project_id}")
        self.assertEqual(page.status_code, 200)

    def test_payment_page_blocked_for_other_customer(self):
        other = User(
            name="Other Customer",
            email="smoke-other@example.com",
            password=generate_password_hash("SmokePass123!"),
            role="customer",
        )
        with self.app.app_context():
            db.session.add(other)
            db.session.commit()
        self._login("smoke-other@example.com", "customer")
        response = self.client.get(
            f"/payment/{self.project_id}", follow_redirects=False
        )
        self.assertEqual(response.status_code, 302)

    # --------------------------------------------------------
    # API
    # --------------------------------------------------------

    def test_api_services(self):
        response = self.client.get("/api/services")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)

    # --------------------------------------------------------
    # PACKAGE_PRICES coverage of project packages in this DB
    # --------------------------------------------------------

    def test_package_prices_covers_project_packages(self):
        with self.app.app_context():
            stored = {p.package for p in Project.query.all()}
        missing = stored - set(PACKAGE_PRICES)
        self.assertFalse(
            missing, f"Packages missing from PACKAGE_PRICES: {missing}"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
