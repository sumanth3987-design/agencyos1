# Security Guide

This document covers security practices for AgencyOS. It is a practical guide, not a guarantee of security. Static documentation does not make the application production-ready.

## Secret Storage and `.env`

- Never commit `.env`, credentials, tokens, API keys, or private keys to version control.
- `.env` is gitignored. Create it locally from `.env.example`.
- Do not copy real secret values into documentation, issues, or pull requests.

## SECRET_KEY

- Generate a unique, high-entropy secret of at least 32 characters for local development.
- Never reuse a production secret in development.
- Example generation (PowerShell):

```powershell
$bytes = [byte[]]::new(32)
$rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()

try {
    $rng.GetBytes($bytes)
    $secret = -join ($bytes | ForEach-Object { $_.ToString('x2') })
    $secret
}
finally {
    $rng.Dispose()
}
```

This generates 32 cryptographically random bytes and outputs 64 hexadecimal characters. The generated secret must remain local and must never be pasted into documentation, chat, or Git.

- Store the generated value in `.env`, not in source code.

## Razorpay Credentials

- `RAZORPAY_KEY_ID` is public-facing and may appear in client-side templates.
- `RAZORPAY_KEY_SECRET` must remain server-side only. Never log it, never include it in frontend code, and never commit it.
- Use Razorpay test mode credentials for local development. Switch to live mode only in production with explicit authorization.
- Verify payment signatures server-side before trusting payment status.

## Session and Cookie Security

- Production (`FLASK_ENV=production`): secure, HttpOnly, SameSite=Lax session cookies.
- Development (`FLASK_ENV=development`): insecure cookies permitted for local HTTP testing. Do not deploy development settings to production.
- Always use HTTPS in production.

## Database and Backups

- The active SQLite database is `instance/agencyos.db` and is gitignored.
- Do not commit database files or rollback copies.
- Do not run database migrations or administrative scripts (`create_admin.py`, `migrate_user_email.py`, `update_database.py`) against the active database without explicit authorization and a validated backup/rollback plan.
- Before any database mutation, create a timestamped backup copy and verify its integrity.

## Secret Exposure

If you suspect a credential has been exposed:

1. Rotate the affected credential immediately through the relevant provider (e.g., Razorpay dashboard).
2. Revoke the old key and generate a new one.
3. Update `.env` with the new value.
4. Review Git history for accidental commits (`.env` is gitignored, but verify no secrets were added to tracked files).
5. Report the incident to the project maintainers.

## Trusted Application Origin

- Set `APP_BASE_URL` to the public HTTPS origin of the deployed application.
- The value must be an absolute HTTP(S) URL with a valid host and no credentials, fragment, query string, or path.
- Production requires HTTPS and fails startup if `APP_BASE_URL` is missing or invalid.
- Password-reset and email-verification links use this origin.

## Rate Limiting

- `RATELIMIT_STORAGE_URL` selects the Flask-Limiter backend. Use `memory://` only for local single-process development and isolated tests.
- Production multi-worker deployments must use shared Redis storage (`redis://` or `rediss://`).
- In-memory storage in production requires `RATELIMIT_ALLOW_IN_MEMORY_STORAGE=true` and is only safe for a single worker.
- Redis URLs must include a hostname. Invalid or unsupported schemes are rejected at startup.

This documentation does not constitute a production readiness review. Do not deploy to production until:
- `SECRET_KEY` is configured with a strong, unique value.
- `FLASK_ENV=production` is set.
- Razorpay live credentials are configured and tested.
- HTTPS is enforced.

## Email Verification

- `EMAIL_VERIFICATION_REQUIRED=false` by default; registration and login work without verification.
- Set `EMAIL_VERIFICATION_REQUIRED=true` only after deciding the legacy-account policy.
- Existing accounts remain unverified unless an explicit, documented migration policy is approved.
- Verification tokens expire after `EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS` and are single-use.

## Password Reset

- Reset tokens are random, stored as SHA-256 hashes, expire after `PASSWORD_RESET_TOKEN_EXPIRY_MINUTES`, and are single-use.
- Successful resets invalidate other outstanding reset tokens and increment `session_version`.
- Passwords must be 8–128 characters and contain both letters and digits.
