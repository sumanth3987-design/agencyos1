# Production Deployment Guide

This guide is a practical checklist for deploying AgencyOS. It describes requirements and recommendations; it is not evidence that a deployment has been tested.

## Supported application server

- Run the Flask application through a production WSGI server such as Gunicorn or Waitress.
- Use a process manager such as systemd, Supervisor, or a container orchestrator to keep the process running.
- `PORT` controls the listen port used by `run.py`; bind the WSGI server to the intended host and port.

## Required environment variables

Set these in the deployment environment. Never commit real values.

- `FLASK_ENV=production`
- `SECRET_KEY`  -  strong, unique, at least 32 characters
- `DATABASE_URL`  -  production database URI; do not rely on the default SQLite path for production workloads
- `RAZORPAY_KEY_ID`
- `RAZORPAY_KEY_SECRET`
- `RATELIMIT_STORAGE_URL`  -  `redis://` or `rediss://` with a hostname
- `RATELIMIT_ALLOW_IN_MEMORY_STORAGE=false` unless a single-worker exception is explicitly approved
- `APP_BASE_URL`  -  public HTTPS origin, no path, query, fragment, or credentials
- `MAIL_BACKEND=smtp`
- `MAIL_SERVER`
- `MAIL_PORT`
- `MAIL_USE_TLS`
- `MAIL_USERNAME`
- `MAIL_PASSWORD`
- `MAIL_DEFAULT_SENDER`
- `MAIL_SUPPRESS_SEND=false`
- `EMAIL_VERIFICATION_REQUIRED`  -  set only after the legacy-account policy is decided
- `PASSWORD_RESET_TOKEN_EXPIRY_MINUTES`
- `EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS`

## HTTPS and trusted origin

- Terminate TLS at the reverse proxy or load balancer and forward HTTPS to the application.
- Set `APP_BASE_URL` to the public HTTPS origin.
- Production startup fails if `APP_BASE_URL` is missing or invalid.

## Redis and rate limiting

- Use shared Redis storage for multi-worker deployments.
- In-memory storage is only for local single-process development and isolated tests.
- Production in-memory storage requires `RATELIMIT_ALLOW_IN_MEMORY_STORAGE=true` and is only safe for one worker.

## SMTP delivery

- Configure SMTP credentials and set `MAIL_SUPPRESS_SEND=false`.
- Verify password-reset and verification emails in a non-production environment before release.
- `MAIL_BACKEND=console` does not deliver real email.

## Health checks and logging

- Configure a reverse-proxy health check against an application route.
- Enable application and server logging; do not log secrets, tokens, or message bodies.
- Monitor 4xx/5xx rates and rate-limit responses.

## Database backup and restore

- Back up the production database before any change.
- Test restore procedures periodically.
- Do not run migrations or administrative scripts against the live database without approval.

## Migration preflight and rollback

- Review `MIGRATION_ACCOUNT_SECURITY.sql` and `MIGRATION_PAYMENT_UNIQUENESS.sql` as proposals only.
- Do not execute migrations without a separately approved database plan.
- Run preflight checks for duplicate and empty payment IDs.
- Apply migrations during an approved maintenance window.
- Keep a verified backup and a rollback plan.
- Verify schema and application behavior after migration.

## Pre-deployment checklist

- [ ] `FLASK_ENV=production`
- [ ] Strong unique `SECRET_KEY`
- [ ] Valid Razorpay credentials
- [ ] Redis configured and reachable
- [ ] `APP_BASE_URL` valid HTTPS origin
- [ ] SMTP configured and tested
- [ ] Database backup completed
- [ ] Migration plan approved if schema changes are needed
- [ ] Tests pass in the deployment environment

## Post-deployment checklist

- [ ] Application starts successfully
- [ ] Login, registration, and password reset work
- [ ] Email delivery works if enabled
- [ ] Payment order creation and verification work
- [ ] Rate limiting uses shared storage
- [ ] Logs contain no secret values
- [ ] Database backup and rollback plan remain available
