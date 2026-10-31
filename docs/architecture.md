# System Architecture — AgencyOS

## 1. Application Topology
AgencyOS is architected as a modular Python/Flask monolith using the Application Factory pattern (`create_app`):

[ Client / Browser ]
│ HTTPS (Session Cookies + CSRF Tokens)
▼
[ Flask Application Factory (create_app) ]
├── Blueprints:
│ ├── auth_bp (/login, /register, /logout)
│ ├── admin_bp (/admin/dashboard, /admin/projects, /admin/customers)
│ ├── customer_bp (/dashboard, /businesses, /customer/profile)
│ ├── professional_bp (/professional/dashboard, /professional/workspace)
│ ├── payments_bp (/payments/checkout, /payments/webhook)
│ └── public_bp (/privacy, /terms, /refund-policy, /contact, /api/free-audit)
├── Security Middleware:
│ ├── Flask-Login (HttpOnly, SameSite=Lax, Secure session cookies)
│ ├── Flask-WTF (CSRF verification on state-changing requests)
│ └── Flask-Limiter (Rate limiting on auth and payment endpoints)
├── Services:
│ ├── RazorpayService (Order creation & HMAC SHA256 webhook verification)
│ ├── InvoicingService (SAC 998311 CGST/SGST/IGST tax calculation)
│ └── AiService (Backend-confined Google Gemini SDK)
└── ORM: SQLAlchemy
│
┌────┴───────────────────────────┐
▼ ▼
[ SQLite / PostgreSQL ] [ External APIs ]
(Local: instance/agencyos.db) (Razorpay, Google Gemini)

## 2. Directory Layout
```text
agencyos1/
├── app/
│   ├── __init__.py           # Application Factory, Core Models & Helpers
│   ├── config.py             # Security, Environment, Timezone & Credentials Validator
│   ├── extensions.py         # SQLAlchemy, LoginManager, CSRF, Limiter
│   ├── routes/               # Modular Flask Blueprints (admin, customer, public, etc.)
│   ├── services/             # Core business logic (Payments, Invoicing, AI)
│   ├── static/               # Uploads & Client Deliverables
│   └── templates/            # Flat Studio Dark Jinja2 Templates
├── docs/                     # 10 Master Documentation Files
├── instance/                 # Protected Local SQLite Database (agencyos.db)
├── tests/                    # Pytest Suite (Smoke, Auth, CSRF, Payments, Workflows)
├── app.py                    # Production WSGI Callable (Gunicorn/Render)
├── run.py                    # Local Development Runner (Port & Debug checks)
├── apply_fund_flow_columns.py# Non-destructive SQLite Schema Migration Script
├── DATABASE_UNIQUENESS_REPORT.md # Unique Indexes & Idempotency Audit
├── DECISIONS.md              # Architecture Decision Log (DEC-001 through DEC-018)
└── README.md                 # Project Overview & Setup Guide