"""Tests for the selective AgencyOS recovery script."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from scripts import recover_agencyos_source as recovery


SCHEMA = r'''
CREATE TABLE user (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    password TEXT NOT NULL,
    role TEXT,
    created_at DATETIME
);

CREATE TABLE customer_profile (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES user(id),
    phone TEXT,
    location TEXT
);

CREATE TABLE professional_profile (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES user(id),
    expertise TEXT NOT NULL,
    experience TEXT NOT NULL,
    created_at DATETIME
);

CREATE TABLE business (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES user(id),
    name TEXT NOT NULL,
    created_at DATETIME
);

CREATE TABLE project (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES user(id),
    service TEXT NOT NULL,
    package TEXT NOT NULL,
    requirements TEXT,
    status TEXT,
    created_at DATETIME,
    business_id INTEGER REFERENCES business(id)
);

CREATE TABLE professional_project_application (
    id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES project(id),
    professional_id INTEGER NOT NULL REFERENCES user(id),
    status TEXT,
    created_at DATETIME
);

CREATE TABLE project_delivery (
    id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES project(id),
    professional_id INTEGER NOT NULL REFERENCES user(id),
    submission_number INTEGER NOT NULL,
    completion_notes TEXT NOT NULL,
    status TEXT NOT NULL,
    submitted_at DATETIME NOT NULL,
    reviewed_at DATETIME
);

CREATE TABLE payment (
    id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES project(id),
    customer_id INTEGER NOT NULL REFERENCES user(id),
    razorpay_order_id TEXT NOT NULL,
    razorpay_payment_id TEXT,
    amount INTEGER NOT NULL,
    currency TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at DATETIME,
    paid_at DATETIME
);

CREATE TABLE chat_message (
    id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES project(id),
    sender_id INTEGER NOT NULL REFERENCES user(id),
    message TEXT NOT NULL,
    created_at DATETIME NOT NULL
);

CREATE TABLE invoice (
    id INTEGER PRIMARY KEY,
    invoice_number TEXT NOT NULL UNIQUE,
    project_id INTEGER NOT NULL REFERENCES project(id),
    customer_id INTEGER NOT NULL REFERENCES user(id),
    gross_amount INTEGER NOT NULL,
    talent_payout INTEGER NOT NULL,
    agency_profit INTEGER NOT NULL,
    tax_amount INTEGER NOT NULL,
    status TEXT NOT NULL,
    created_at DATETIME NOT NULL
);

CREATE TABLE notification (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES user(id),
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    is_read INTEGER NOT NULL,
    created_at DATETIME NOT NULL
);
'''


def create_empty_db(path: Path) -> None:
    conn = sqlite3.connect(str(path))
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def insert_user(conn, user_id, name, email, role="customer", created_at=None):
    conn.execute(
        "INSERT INTO user (id, name, email, password, role, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, name, email, "hashed-password", role, created_at),
    )


def fk_issues(conn):
    return conn.execute("PRAGMA foreign_key_check").fetchall()


@pytest.fixture
def source_db(tmp_path: Path) -> Path:
    path = tmp_path / "source.db"
    create_empty_db(path)
    return path


@pytest.fixture
def target_db(tmp_path: Path) -> Path:
    path = tmp_path / "target.db"
    create_empty_db(path)
    conn = sqlite3.connect(str(path))
    insert_user(conn, 1, "Admin", "admin@example.com", role="admin")
    conn.commit()
    conn.close()
    return path
def test_collision_remapping_and_admin_preservation(source_db, target_db):
    sconn = sqlite3.connect(str(source_db))
    for uid in (1, 2, 3):
        insert_user(sconn, uid, f"Source User {uid}", f"source{uid}@example.com")
    sconn.execute(
        "INSERT INTO customer_profile (id, user_id, phone, location) VALUES (?, ?, ?, ?)",
        (1, 1, "123", "City"),
    )
    sconn.commit()
    sconn.close()

    summary = recovery.run_migration(source_db, target_db, recovery.DEFAULT_MIGRATION_TIMESTAMP)

    assert summary["user_id_map"][1] != 1
    assert summary["user_id_map"][1] >= 4

    tconn = sqlite3.connect(str(target_db))
    tconn.execute("PRAGMA foreign_keys = ON")
    admin = tconn.execute("SELECT name, email, role, password FROM user WHERE id = 1").fetchone()
    assert admin == ("Admin", "admin@example.com", "admin", "hashed-password")
    remapped = tconn.execute(
        "SELECT name, password FROM user WHERE id = ?", (summary["user_id_map"][1],)
    ).fetchone()
    assert remapped == ("Source User 1", "hashed-password")
    profile = tconn.execute(
        "SELECT user_id FROM customer_profile WHERE id = 1"
    ).fetchone()
    assert profile == (summary["user_id_map"][1],)
    assert fk_issues(tconn) == []
    tconn.close()


def test_timestamp_normalization_related_and_fallback(source_db, target_db):
    sconn = sqlite3.connect(str(source_db))
    insert_user(sconn, 1, "Source User", "source@example.com")
    sconn.execute(
        "INSERT INTO project (id, customer_id, service, package, requirements, status, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (1, 1, "Svc", "Pkg", "Req", "Pending", None),
    )
    sconn.execute(
        "INSERT INTO payment (id, project_id, customer_id, razorpay_order_id, amount, currency, status, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (1, 1, 1, "order_ts_1", 100, "INR", "Created", "2024-02-02 10:00:00"),
    )
    sconn.execute(
        "INSERT INTO project (id, customer_id, service, package, requirements, status, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (2, 1, "Svc2", "Pkg2", "Req2", "Pending", None),
    )
    sconn.commit()
    sconn.close()

    migration_ts = "2020-01-01 00:00:00"
    summary = recovery.run_migration(source_db, target_db, migration_ts)
    assert summary["normalized_projects"] == 2
    assert summary["normalized_related"] == 1
    assert summary["normalized_fallback"] == 1

    tconn = sqlite3.connect(str(target_db))
    first = tconn.execute("SELECT created_at FROM project WHERE id = 1").fetchone()[0]
    second = tconn.execute("SELECT created_at FROM project WHERE id = 2").fetchone()[0]
    assert first == "2024-02-02 10:00:00"
    assert second == migration_ts
    tconn.close()
def test_payment_preservation_and_fields(source_db, target_db):
    sconn = sqlite3.connect(str(source_db))
    insert_user(sconn, 1, "Source User", "source@example.com")
    sconn.execute(
        "INSERT INTO project (id, customer_id, service, package, requirements, status, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (1, 1, "Svc", "Pkg", "Req", "Pending", "2024-01-01 00:00:00"),
    )
    sconn.execute(
        "INSERT INTO payment (id, project_id, customer_id, razorpay_order_id, razorpay_payment_id, amount, currency, status, created_at, paid_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (1, 1, 1, "order_pay_1", "pay_1", 4999, "INR", "Paid", "2024-01-02 00:00:00", "2024-01-03 00:00:00"),
    )
    sconn.commit()
    sconn.close()

    summary = recovery.run_migration(source_db, target_db, recovery.DEFAULT_MIGRATION_TIMESTAMP)
    assert summary["empty_payment_ids"] == 0

    tconn = sqlite3.connect(str(target_db))
    row = tconn.execute(
        "SELECT project_id, customer_id, razorpay_order_id, razorpay_payment_id, amount, currency, status, created_at, paid_at "
        "FROM payment WHERE id = 1"
    ).fetchone()
    remapped_user = summary["user_id_map"][1]
    assert row[0] == 1
    assert row[1] == remapped_user
    assert row[2] == "order_pay_1"
    assert row[3] == "pay_1"
    assert row[4] == 4999
    assert row[5] == "INR"
    assert row[6] == "Paid"
    assert row[7] == "2024-01-02 00:00:00"
    assert row[8] == "2024-01-03 00:00:00"
    tconn.close()


def test_duplicate_emails_are_preserved(source_db, target_db):
    sconn = sqlite3.connect(str(source_db))
    insert_user(sconn, 1, "Source Admin", "duplicate@example.com")
    insert_user(sconn, 2, "Source Admin Two", "duplicate@example.com")
    sconn.commit()
    sconn.close()

    summary = recovery.run_migration(source_db, target_db, recovery.DEFAULT_MIGRATION_TIMESTAMP)
    assert summary["user_id_map"][1] != 1

    tconn = sqlite3.connect(str(target_db))
    emails = [r[0] for r in tconn.execute("SELECT email FROM user").fetchall()]
    assert emails.count("duplicate@example.com") == 2
    tconn.close()


def test_uniqueness_failure_rolls_back(source_db, target_db):
    sconn = sqlite3.connect(str(source_db))
    insert_user(sconn, 1, "Source User", "source@example.com")
    sconn.execute(
        "INSERT INTO project (id, customer_id, service, package, requirements, status, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (1, 1, "Svc", "Pkg", "Req", "Pending", "2024-01-01 00:00:00"),
    )
    sconn.execute(
        "INSERT INTO payment (id, project_id, customer_id, razorpay_order_id, amount, currency, status) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (1, 1, 1, "dup_order", 100, "INR", "Created"),
    )
    sconn.execute(
        "INSERT INTO payment (id, project_id, customer_id, razorpay_order_id, amount, currency, status) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (2, 1, 1, "dup_order", 200, "INR", "Created"),
    )
    sconn.commit()
    sconn.close()

    before = sqlite3.connect(str(target_db)).execute("SELECT COUNT(*) FROM user").fetchone()[0]
    with pytest.raises(RuntimeError):
        recovery.run_migration(source_db, target_db, recovery.DEFAULT_MIGRATION_TIMESTAMP)
    after = sqlite3.connect(str(target_db)).execute("SELECT COUNT(*) FROM user").fetchone()[0]
    assert before == after
def test_pk_collision_rolls_back(source_db, target_db):
    sconn = sqlite3.connect(str(source_db))
    insert_user(sconn, 1, "Source User", "source@example.com")
    sconn.execute(
        "INSERT INTO project (id, customer_id, service, package, requirements, status, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (1, 1, "Svc", "Pkg", "Req", "Pending", "2024-01-01 00:00:00"),
    )
    sconn.commit()
    sconn.close()

    tconn = sqlite3.connect(str(target_db))
    tconn.execute(
        "INSERT INTO project (id, customer_id, service, package, requirements, status, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (1, 1, "Existing", "Pkg", "Req", "Pending", "2024-01-01 00:00:00"),
    )
    tconn.commit()
    tconn.close()

    with pytest.raises(RuntimeError):
        recovery.run_migration(source_db, target_db, recovery.DEFAULT_MIGRATION_TIMESTAMP)


def test_foreign_key_validation_failure(source_db, target_db):
    sconn = sqlite3.connect(str(source_db))
    insert_user(sconn, 1, "Source User", "source@example.com")
    sconn.execute(
        "INSERT INTO payment (id, project_id, customer_id, razorpay_order_id, amount, currency, status) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (1, 999, 1, "order_fk", 100, "INR", "Created"),
    )
    sconn.commit()
    sconn.close()

    with pytest.raises(RuntimeError):
        recovery.run_migration(source_db, target_db, recovery.DEFAULT_MIGRATION_TIMESTAMP)


def test_idempotency_refusal(source_db, target_db):
    sconn = sqlite3.connect(str(source_db))
    insert_user(sconn, 1, "Source User", "source@example.com")
    sconn.execute(
        "INSERT INTO project (id, customer_id, service, package, requirements, status, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (1, 1, "Svc", "Pkg", "Req", "Pending", "2024-01-01 00:00:00"),
    )
    sconn.commit()
    sconn.close()

    recovery.run_migration(source_db, target_db, recovery.DEFAULT_MIGRATION_TIMESTAMP)
    with pytest.raises(RuntimeError):
        recovery.run_migration(source_db, target_db, recovery.DEFAULT_MIGRATION_TIMESTAMP)


def test_fk_check_clean_after_recovery(source_db, target_db):
    sconn = sqlite3.connect(str(source_db))
    insert_user(sconn, 1, "Source User", "source@example.com")
    sconn.execute(
        "INSERT INTO project (id, customer_id, service, package, requirements, status, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (1, 1, "Svc", "Pkg", "Req", "Pending", "2024-01-01 00:00:00"),
    )
    sconn.execute(
        "INSERT INTO professional_project_application (id, project_id, professional_id, status, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (1, 1, 1, "Applied", "2024-01-01 00:00:00"),
    )
    sconn.commit()
    sconn.close()

    recovery.run_migration(source_db, target_db, recovery.DEFAULT_MIGRATION_TIMESTAMP)

    tconn = sqlite3.connect(str(target_db))
    tconn.execute("PRAGMA foreign_keys = ON")
    assert tconn.execute("PRAGMA foreign_key_check").fetchall() == []
    tconn.close()


def test_unsafe_paths():
    original = Path(r"D:\AgencyOS\instance\agencyos.db")
    backup = Path(r"D:\AgencyOS1_recovery_backups\20261027_010754\source.db")
    assert recovery.is_protected(original)[0] is True
    assert recovery.is_protected(backup)[0] is True

    dummy = Path(__file__).resolve().parent / "dummy.db"
    create_empty_db(dummy)
    try:
        import sys as _sys

        _sys.argv = [
            "recover_agencyos_source.py",
            "--source-copy",
            str(dummy),
            "--target-copy",
            str(dummy),
            "--confirm-disposable-target",
        ]
        assert recovery.main() == 1
    finally:
        dummy.unlink(missing_ok=True)

def test_password_hash_mismatch_detection(source_db, target_db):
    sconn = sqlite3.connect(str(source_db))
    insert_user(sconn, 1, "Source User", "source@example.com")
    sconn.commit()
    sconn.close()

    summary = recovery.run_migration(source_db, target_db, recovery.DEFAULT_MIGRATION_TIMESTAMP)

    tconn = sqlite3.connect(str(target_db))
    tconn.execute("PRAGMA foreign_keys = ON")
    baseline = recovery.capture_admin_baseline(tconn)
    tconn.execute(
        "UPDATE user SET password = ? WHERE id = ?",
        ("tampered-hash", summary["user_id_map"][1]),
    )
    tconn.commit()

    sconn = sqlite3.connect(str(source_db))
    with pytest.raises(RuntimeError):
        recovery.validate_imported_users(sconn, tconn, summary["user_id_map"], baseline)
    tconn.close()
    sconn.close()


def test_admin_preservation(source_db, target_db):
    sconn = sqlite3.connect(str(source_db))
    insert_user(sconn, 1, "Source User", "source@example.com")
    sconn.commit()
    sconn.close()

    summary = recovery.run_migration(source_db, target_db, recovery.DEFAULT_MIGRATION_TIMESTAMP)

    tconn = sqlite3.connect(str(target_db))
    tconn.execute("PRAGMA foreign_keys = ON")
    baseline = recovery.capture_admin_baseline(tconn)
    tconn.execute(
        "UPDATE user SET name = ?, role = ?, password = ? WHERE id = 1",
        ("Tampered Admin", "customer", "tampered-hash"),
    )
    tconn.commit()

    sconn = sqlite3.connect(str(source_db))
    with pytest.raises(RuntimeError):
        recovery.validate_imported_users(sconn, tconn, summary["user_id_map"], baseline)
    tconn.close()
    sconn.close()
def test_payment_field_mismatch_detection(source_db, target_db):
    sconn = sqlite3.connect(str(source_db))
    insert_user(sconn, 1, "Source User", "source@example.com")
    sconn.execute(
        "INSERT INTO project (id, customer_id, service, package, requirements, status, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (1, 1, "Svc", "Pkg", "Req", "Pending", "2024-01-01 00:00:00"),
    )
    sconn.execute(
        "INSERT INTO payment (id, project_id, customer_id, razorpay_order_id, razorpay_payment_id, amount, currency, status, created_at, paid_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (1, 1, 1, "order_pay_1", "pay_1", 4999, "INR", "Paid", "2024-01-02 00:00:00", "2024-01-03 00:00:00"),
    )
    sconn.commit()
    sconn.close()

    summary = recovery.run_migration(source_db, target_db, recovery.DEFAULT_MIGRATION_TIMESTAMP)

    tconn = sqlite3.connect(str(target_db))
    tconn.execute("UPDATE payment SET amount = ? WHERE id = ?", (1, 1))
    tconn.commit()

    sconn = sqlite3.connect(str(source_db))
    with pytest.raises(RuntimeError):
        recovery.validate_imported_payments(sconn, tconn, summary["user_id_map"])
    tconn.close()
    sconn.close()


def test_source_hash_mismatch(source_db, target_db):
    sconn = sqlite3.connect(str(source_db))
    insert_user(sconn, 1, "Source User", "source@example.com")
    sconn.commit()
    sconn.close()

    tconn = sqlite3.connect(str(target_db))
    before = tconn.execute("SELECT COUNT(*) FROM user").fetchone()[0]
    tconn.close()

    with pytest.raises(RuntimeError):
        recovery.run_migration(
            source_db,
            target_db,
            recovery.DEFAULT_MIGRATION_TIMESTAMP,
            "0" * 64,
        )

    tconn = sqlite3.connect(str(target_db))
    after = tconn.execute("SELECT COUNT(*) FROM user").fetchone()[0]
    tconn.close()
    assert after == before
def test_optional_table_rejection(source_db, target_db):
    sconn = sqlite3.connect(str(source_db))
    insert_user(sconn, 1, "Source User", "source@example.com")
    sconn.execute(
        "INSERT INTO project (id, customer_id, service, package, requirements, status, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (1, 1, "Svc", "Pkg", "Req", "Pending", "2024-01-01 00:00:00"),
    )
    sconn.execute(
        "INSERT INTO chat_message (id, project_id, sender_id, message, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (1, 1, 1, "hello", "2024-01-01 00:00:00"),
    )
    sconn.commit()
    sconn.close()

    tconn = sqlite3.connect(str(target_db))
    before = tconn.execute("SELECT COUNT(*) FROM user").fetchone()[0]
    tconn.close()

    with pytest.raises(RuntimeError):
        recovery.run_migration(source_db, target_db, recovery.DEFAULT_MIGRATION_TIMESTAMP)

    tconn = sqlite3.connect(str(target_db))
    after = tconn.execute("SELECT COUNT(*) FROM user").fetchone()[0]
    tconn.close()
    assert after == before


def test_invoice_optional_table_rejection(source_db, target_db):
    sconn = sqlite3.connect(str(source_db))
    insert_user(sconn, 1, "Source User", "source@example.com")
    sconn.execute(
        "INSERT INTO project (id, customer_id, service, package, requirements, status, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (1, 1, "Svc", "Pkg", "Req", "Pending", "2024-01-01 00:00:00"),
    )
    sconn.execute(
        "INSERT INTO invoice (id, invoice_number, project_id, customer_id, gross_amount, talent_payout, agency_profit, tax_amount, status, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (1, "INV-1", 1, 1, 100, 80, 20, 0, "Paid", "2024-01-01 00:00:00"),
    )
    sconn.commit()
    sconn.close()

    with pytest.raises(RuntimeError):
        recovery.run_migration(source_db, target_db, recovery.DEFAULT_MIGRATION_TIMESTAMP)


def test_notification_optional_table_rejection(source_db, target_db):
    sconn = sqlite3.connect(str(source_db))
    insert_user(sconn, 1, "Source User", "source@example.com")
    sconn.execute(
        "INSERT INTO notification (id, user_id, title, message, is_read, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (1, 1, "Title", "Message", 0, "2024-01-01 00:00:00"),
    )
    sconn.commit()
    sconn.close()

    with pytest.raises(RuntimeError):
        recovery.run_migration(source_db, target_db, recovery.DEFAULT_MIGRATION_TIMESTAMP)


def test_case_insensitive_email_collision(source_db, target_db):
    sconn = sqlite3.connect(str(source_db))
    insert_user(sconn, 1, "Source User", "Admin@Example.com")
    sconn.commit()
    sconn.close()

    tconn = sqlite3.connect(str(target_db))
    tconn.execute("UPDATE user SET email = ? WHERE id = 1", ("admin@example.com",))
    tconn.commit()
    tconn.close()

    with pytest.raises(RuntimeError):
        recovery.run_migration(source_db, target_db, recovery.DEFAULT_MIGRATION_TIMESTAMP)