# AgencyOS

AgencyOS is a digital-services marketplace for website design and SEO services. The platform provides customer, professional, and admin portals with project scoping, Razorpay payment integration, role-based authentication, and project lifecycle management.

## Architecture

AgencyOS consists of two separate, unconnected applications:

### 1. Flask Backend (Primary Application)

The actual AgencyOS service is a Flask web application:

- **Framework:** Flask, Python
- **Templating:** Jinja2 (`templates/`)
- **Database:** Flask-SQLAlchemy with SQLite by default (`instance/agencyos.db`)
- **Authentication:** Flask-Login with Werkzeug password hashing
- **CSRF protection:** Flask-WTF CSRFProtect
- **Payments:** Razorpay integration
- **Entry point:** `python run.py`

#### Directory overview

| Directory | Purpose |
|-----------|---------|
| `app/` | Flask application package: configuration, extensions, models, blueprints, utilities |
| `app/blueprints/` | Route blueprints: auth, customer, professional, admin, payments, api, collaboration |
| `templates/` | Jinja2 HTML templates for server-rendered pages |
| `static/` | Static CSS and JavaScript assets |
| `tests/` | Pytest test suite |

### 2. React/Vite Demo (Unconnected)

A separate React/Vite application exists under `src/` for AI Studio demonstration purposes. It:

- Uses hardcoded mock data (`src/data/mockData.ts`)
- Is **not integrated** with the Flask backend
- Makes **no API calls** to Flask
- Is run independently with `npm run dev` (port 3000)

Do not use the React/Vite demo as the AgencyOS backend.

## Prerequisites

- Python 3 (with `venv` module)
- Node.js and npm (only for the React/Vite demo)

## Backend Setup (Windows)

1. Create and activate a virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. Install Python dependencies:

```powershell
pip install -r requirements.txt
```

3. Configure environment variables:

Copy `.env.example` to `.env` and fill in the required values. Never commit `.env`.

```powershell
copy .env.example .env
```

4. Run the Flask application:

```powershell
python run.py
```

The application starts on `http://0.0.0.0:5000` by default (port configurable via `PORT` environment variable).

## Environment Configuration

Configure the following in `.env` (template in `.env.example`):

| Variable | Purpose | Default |
|----------|---------|---------|
| `SECRET_KEY` | Flask session signing secret (required, at least 32 characters) | None |
| `FLASK_ENV` | `development` or `production` | `production` if unset |
| `DATABASE_URL` | SQLAlchemy database URI | `sqlite:///agencyos.db` |
| `RAZORPAY_KEY_ID` | Razorpay public key ID | Placeholder |
| `RAZORPAY_KEY_SECRET` | Razorpay secret key (server-side only) | Placeholder |
| `RATELIMIT_STORAGE_URL` | Flask-Limiter storage URL (`memory://` or `redis://...`) | `memory://` |
| `MAIL_BACKEND` | Email backend (`console` or `smtp`) | `console` |
| `MAIL_SERVER` | SMTP server hostname | empty |
| `MAIL_PORT` | SMTP server port | `587` |
| `MAIL_USE_TLS` | Enable STARTTLS for SMTP | `true` |
| `MAIL_USERNAME` | SMTP username | empty |
| `MAIL_PASSWORD` | SMTP password (server-side only) | empty |
| `MAIL_DEFAULT_SENDER` | Default email sender address | `no-reply@agencyos.local` |
| `MAIL_SUPPRESS_SEND` | Suppress outbound email delivery | `false` |

Never commit `.env`. It is gitignored.

## Testing

Run the Python test suite:

```powershell
python -m pytest tests/ -q
```

The default test fixture uses an in-memory SQLite database. An explicitly configured `TEST_DATABASE_URL` can select a dedicated PostgreSQL test database. PostgreSQL tests must use a dedicated database satisfying the project's existing test-database safeguards. This documentation does not guarantee that every possible test or configuration can never affect another database; verify your test environment before running the full suite.

## React/Vite Demo (Optional)

The React/Vite demo is a standalone mock-data application. It is not required to run AgencyOS.

```powershell
npm install
npm run dev
```

The demo runs on port 3000 and does not connect to the Flask backend.

## Gemini AI

Gemini AI functionality is **deferred** and is not implemented in this codebase. Do not present Gemini features as available.

## Development vs Production

- **Development:** `FLASK_ENV=development` enables debug mode and insecure session cookies (not secure over HTTP).
- **Production:** `FLASK_ENV=production` requires a strong `SECRET_KEY`, secure session cookies, and valid Razorpay credentials. Do not run in production with development settings.
