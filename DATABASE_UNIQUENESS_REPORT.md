# Database Uniqueness and Payment Concurrency Report

## 1. Summary

This report reflects the current working-tree implementation. The migration
proposal has **not** been executed, and no database schema or rows have been
changed by this audit or by Batch 1.

## 2. Files Inspected

- `app/models/__init__.py`
- `app/blueprints/payments/__init__.py`
- `tests/test_payments.py`
- `tests/conftest.py`
- `MIGRATION_PAYMENT_UNIQUENESS.sql`
- `DATABASE_UNIQUENESS_REPORT.md`

## 3. SQLAlchemy Payment Uniqueness Protections

Table name: `payment`

1. `uq_payment_razorpay_order_id`
   - Type: unique constraint
   - Columns: `razorpay_order_id`
   - Scope: all rows

2. `uq_payment_razorpay_payment_id_partial`
   - Type: partial unique index
   - Columns: `razorpay_payment_id`
   - Predicate: `razorpay_payment_id IS NOT NULL`
   - Allows multiple NULL payment IDs.

3. `uq_payment_project_customer_created`
   - Type: partial unique index
   - Columns: `project_id`, `customer_id`
   - Predicate: `status = 'Created'`
   - Allows multiple non-`Created` payments for the same project/customer.

These are defined in `Payment.__table_args__` in `app/models/__init__.py`.

## 4. Test Database Configuration

- Tests use an in-memory SQLite database: `sqlite:///:memory:`.
- `tests/conftest.py` calls `db.create_all()`, so the partial indexes above
  are created in the test database.
- Tests are guarded against non-memory databases by `assert_test_database`.
- Opt-in PostgreSQL testing is available through `TEST_DATABASE_URL`. When set,
  it must use the approved `postgresql+psycopg` driver and target a dedicated
  database whose name ends in `_test` or `_ci`. The suite fails closed if
  PostgreSQL is unavailable and never falls back to SQLite.
- `requirements.txt` includes `psycopg[binary]==3.3.6` for this opt-in profile.

## 5. Test Results

- Focused payment tests: `36 passed`, `5 warnings`.
- Full suite result: `142 passed`, `0 failed`, `6 skipped`, `50 warnings`,
  runtime `70.37s`.
- The 6 skipped tests are the opt-in PostgreSQL-specific tests; they are skipped
  because `psycopg` and a dedicated PostgreSQL test database are not available.
- PostgreSQL tests and migration execution remain unverified.
- Warnings are pre-existing dependency and SQLAlchemy legacy-API deprecation
  warnings, not failures.

## 6. Conflict Testing Categories

- Deterministic conflict tests: run sequentially against one in-memory
  SQLite connection/session. They verify constraint rejection, NULL
  handling, rollback, and idempotent recovery.
- Simulated race tests: monkeypatch `session.commit` to raise `IntegrityError`.
  These verify recovery behavior, not real concurrent database access.
- Genuine multi-connection concurrency: requires separate connections/sessions
  and a file-backed SQLite database or PostgreSQL. SQLite in-memory tests do
  not establish PostgreSQL concurrency behavior.

## 7. Migration Status

- `MIGRATION_PAYMENT_UNIQUENESS.sql` is a proposal only.
- It has not been executed.
- Existing databases still require a separately approved migration.
- Active production databases are not protected by the partial unique indexes
  until that migration is applied.

## 8. Migration Corrections Made in Batch 1

- Added preflight query `1e` for empty `razorpay_order_id` values.
- Added PostgreSQL DO-block guard that aborts when empty
  `razorpay_order_id` values exist.
- Removed the invalid SQLite guard that referenced
  `__migration_preflight_failed__`.
- Replaced the invalid SQLite guard with explicit operator verification
  instructions.
- Added pre-normalization count capture guidance for empty payment IDs.
- Added post-migration count verification guidance.
- Added index/constraint definition verification guidance.
- Added backup, test-on-copy, and failure-recovery instructions.
- Added explicit statements that the SQL has not been executed or validated
  against PostgreSQL or SQLite.

## 9. Required Preflight and Backup Steps

Before any future migration execution:

1. Back up the target database.
2. Run all preflight queries in section 1 of the migration file.
3. Require zero rows for:
   - duplicate non-NULL `razorpay_order_id`
   - duplicate non-NULL `razorpay_payment_id`
   - multiple `Created` payments per project/customer
   - empty `razorpay_order_id`
4. Review empty `razorpay_payment_id` rows before normalization.
5. Record `empty_payment_ids_before_normalization`.
6. Compare existing index/constraint definitions with the intended definitions.
7. Test the migration on a copy of the database.
8. Apply only during an approved maintenance window.

## 10. PostgreSQL Compatibility

- PostgreSQL compatibility is unverified until tested against PostgreSQL.
- No PostgreSQL driver is currently installed in this environment.
- PostgreSQL was not reachable on port 5432 during the read-only check.
- The SQLAlchemy definitions use both `postgresql_where` and `sqlite_where`.
- The migration SQL uses PostgreSQL-compatible partial index syntax, but it
  has not been executed or validated against PostgreSQL.
- Batch 4A added an opt-in PostgreSQL test profile and the `psycopg[binary]`
  dependency. PostgreSQL-specific tests now exist but have not been executed
  in this environment because no dedicated PostgreSQL test database or driver
  is available.

- PostgreSQL execution and validation remain outstanding.

## 11. Production Readiness

Production readiness is **not claimed**. Remaining blockers include:

- Git reconciliation of staged and unstaged changes.
- Active database migration.
- Genuine concurrency verification.
- PostgreSQL validation.
- Batch 4A-4D changes are implemented in the working tree but are not staged,
  committed, or validated against PostgreSQL.

- Final Git review.
