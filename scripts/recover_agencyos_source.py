#!/usr/bin/env python3
"""Selective recovery of AgencyOS source data into a disposable target copy."""

from __future__ import annotations

import argparse
import hashlib
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path


ORIGINAL_PATHS = {
    Path(r"D:\AgencyOS\instance\agencyos.db").resolve(),
    Path(r"D:\AgencyOS1\instance\agencyos.db").resolve(),
}
BACKUP_ROOT = Path(r"D:\AgencyOS1_recovery_backups").resolve()
PROTECTED_DIRECTORIES = {
    Path(r"D:\AgencyOS\instance").resolve(),
    Path(r"D:\AgencyOS1\instance").resolve(),
    BACKUP_ROOT,
}

EXPECTED_TABLES = [
    "user", "customer_profile", "professional_profile", "business", "project",
    "professional_project_application", "project_delivery", "payment",
    "chat_message", "invoice", "notification",
]
CORE_TABLES = [
    "user", "customer_profile", "professional_profile", "business", "project",
    "professional_project_application", "project_delivery", "payment",
]
OPTIONAL_TABLES = ["chat_message", "invoice", "notification"]
IMPORT_ORDER = [
    "user", "customer_profile", "professional_profile", "business", "project",
    "professional_project_application", "project_delivery", "payment",
    "chat_message", "invoice", "notification",
]
DEFAULT_MIGRATION_TIMESTAMP = "2026-10-27 00:00:00"


def q(identifier):
    return '"' + str(identifier).replace('"', '""') + '"'


def fail(message):
    raise RuntimeError(message)


def parse_timestamp(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        try:
            return datetime.fromisoformat(text.replace(" ", "T", 1))
        except ValueError:
            return None


def resolve_path(value):
    return Path(value).expanduser().resolve()


def is_protected(path):
    if path in ORIGINAL_PATHS:
        return True, "one of the original AgencyOS databases"
    for protected_dir in PROTECTED_DIRECTORIES:
        try:
            path.relative_to(protected_dir)
            return True, "inside a protected original or backup directory"
        except ValueError:
            continue
    return False, ""


def table_names(conn):
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    return {r[0] for r in rows}


def table_info(conn, table):
    return conn.execute(f"PRAGMA table_info({q(table)})").fetchall()


def col_names(conn, table):
    return [r[1] for r in table_info(conn, table)]


def pk_column(conn, table):
    for row in table_info(conn, table):
        if row[5]:
            return row[1]
    return "id"


def normalize_colinfo(conn, table):
    return [(r[1], r[2], r[3], r[4], r[5]) for r in table_info(conn, table)]


def fetch_rows(conn, table):
    columns = col_names(conn, table)
    sql = "SELECT " + ", ".join(q(c) for c in columns) + " FROM " + q(table)
    rows = conn.execute(sql).fetchall()
    return columns, [dict(zip(columns, row)) for row in rows]


def count_rows(conn, table):
    return conn.execute(f"SELECT COUNT(*) FROM {q(table)}").fetchone()[0]


def string_length_limit(column_type):
    match = re.search(r"\((\d+)\)", column_type or "")
    if not match:
        return None
    return int(match.group(1))


def validate_row(table, columns_info, row):
    info_by_name = {r[1]: r for r in columns_info}
    for col, value in row.items():
        r = info_by_name.get(col)
        if r is None:
            continue
        _cid, _name, col_type, notnull, dflt_value, _pk = r
        if notnull and value is None and dflt_value is None:
            fail(f"Required field {table}.{col} is NULL")
        limit = string_length_limit(col_type)
        if limit is not None and value is not None:
            if len(str(value)) > limit:
                fail(
                    f"String length exceeds limit for {table}.{col}: "
                    f"{len(str(value))} > {limit}"
                )


def enable_foreign_keys(conn, label):
    conn.execute("PRAGMA foreign_keys = ON")
    value = conn.execute("PRAGMA foreign_keys").fetchone()[0]
    if value != 1:
        fail(f"Could not enable foreign-key enforcement on {label} database")
def verify_schema(source_conn, target_conn):
    source_tables = table_names(source_conn)
    target_tables = table_names(target_conn)

    missing_source = [t for t in EXPECTED_TABLES if t not in source_tables]
    if missing_source:
        fail(f"Source database missing expected tables: {missing_source}")

    missing_core = [t for t in CORE_TABLES if t not in target_tables]
    if missing_core:
        fail(f"Target database missing required tables: {missing_core}")

    for table in OPTIONAL_TABLES:
        if table in source_tables and table not in target_tables:
            if count_rows(source_conn, table) > 0:
                fail(f"Source has rows in {table}, but target does not have that table")

    common_tables = sorted(source_tables & target_tables)
    for table in common_tables:
        source_cols = normalize_colinfo(source_conn, table)
        target_cols = normalize_colinfo(target_conn, table)
        source_names = {c[0] for c in source_cols}
        target_names = {c[0] for c in target_cols}
        if not source_names.issubset(target_names):
            fail(
                f"Target missing source columns for table {table}: "
                f"{sorted(source_names - target_names)}"
            )

        source_fks = sorted(source_conn.execute(
            f"PRAGMA foreign_key_list({q(table)})"
        ).fetchall())
        target_fks = sorted(target_conn.execute(
            f"PRAGMA foreign_key_list({q(table)})"
        ).fetchall())

        def fk_key(row):
            # row: (id, seq, table, from, to, on_update, on_delete, match)
            return (row[2], row[3], row[4], row[5], row[6], row[7])

        source_fk_keys = {fk_key(r) for r in source_fks}
        target_fk_keys = {fk_key(r) for r in target_fks}
        if not source_fk_keys.issubset(target_fk_keys):
            fail(f"Foreign-key schema mismatch for table {table}")


def check_primary_key_collisions(source_conn, target_conn):
    source_tables = table_names(source_conn)
    target_tables = table_names(target_conn)
    for table in IMPORT_ORDER:
        if table not in source_tables or table not in target_tables:
            continue
        if table == "user":
            continue
        if count_rows(source_conn, table) == 0:
            continue
        pk = pk_column(source_conn, table)
        source_ids = [r[0] for r in source_conn.execute(
            f"SELECT {q(pk)} FROM {q(table)}"
        ).fetchall()]
        if not source_ids:
            continue
        placeholders = ", ".join("?" for _ in source_ids)
        existing = target_conn.execute(
            f"SELECT {q(pk)} FROM {q(table)} WHERE {q(pk)} IN ({placeholders})",
            source_ids,
        ).fetchall()
        if existing:
            fail(
                f"Unexpected primary-key collision or prior recovery in {table}: "
                f"{len(existing)} matching primary key(s)"
            )
def check_payment_uniqueness(source_conn, target_conn):
    duplicate_orders = source_conn.execute(
        """
        SELECT razorpay_order_id, COUNT(*) AS c
        FROM payment
        WHERE razorpay_order_id IS NOT NULL
        GROUP BY razorpay_order_id
        HAVING COUNT(*) > 1
        """
    ).fetchall()
    if duplicate_orders:
        fail("Source has duplicate non-NULL razorpay_order_id values")

    duplicate_payments = source_conn.execute(
        """
        SELECT razorpay_payment_id, COUNT(*) AS c
        FROM payment
        WHERE razorpay_payment_id IS NOT NULL
        GROUP BY razorpay_payment_id
        HAVING COUNT(*) > 1
        """
    ).fetchall()
    if duplicate_payments:
        fail("Source has duplicate non-NULL razorpay_payment_id values")

    duplicate_created = source_conn.execute(
        """
        SELECT project_id, customer_id, COUNT(*) AS c
        FROM payment
        WHERE status = 'Created'
        GROUP BY project_id, customer_id
        HAVING COUNT(*) > 1
        """
    ).fetchall()
    if duplicate_created:
        fail("Source has multiple Created payments for the same project/customer")

    empty_order_ids = source_conn.execute(
        "SELECT COUNT(*) FROM payment WHERE razorpay_order_id = ''"
    ).fetchone()[0]
    if empty_order_ids:
        fail("Source has empty-string razorpay_order_id values")

    empty_payment_ids = source_conn.execute(
        "SELECT COUNT(*) FROM payment WHERE razorpay_payment_id = ''"
    ).fetchone()[0]

    if count_rows(target_conn, "payment") > 0:
        source_orders = [r[0] for r in source_conn.execute(
            "SELECT razorpay_order_id FROM payment"
        ).fetchall()]
        target_orders = {r[0] for r in target_conn.execute(
            "SELECT razorpay_order_id FROM payment"
        ).fetchall()}
        if [v for v in source_orders if v in target_orders]:
            fail("Source payment order IDs already exist in target")

        source_payment_ids = [r[0] for r in source_conn.execute(
            "SELECT razorpay_payment_id FROM payment WHERE razorpay_payment_id IS NOT NULL"
        ).fetchall()]
        target_payment_ids = {r[0] for r in target_conn.execute(
            "SELECT razorpay_payment_id FROM payment WHERE razorpay_payment_id IS NOT NULL"
        ).fetchall()}
        if [v for v in source_payment_ids if v in target_payment_ids]:
            fail("Source payment IDs already exist in target")

    return empty_payment_ids
def build_user_id_map(source_conn, target_conn):
    source_user_ids = [r[0] for r in source_conn.execute(
        "SELECT id FROM user ORDER BY id"
    ).fetchall()]
    target_user_ids = [r[0] for r in target_conn.execute(
        "SELECT id FROM user ORDER BY id"
    ).fetchall()]
    target_user_set = set(target_user_ids)

    for source_id in source_user_ids:
        if source_id in target_user_set and source_id != 1:
            fail(f"Unexpected user primary-key collision: {source_id}")

    used_ids = set(target_user_ids)
    user_id_map = {}
    max_id = max(target_user_ids + source_user_ids) if (target_user_ids or source_user_ids) else 0

    for source_id in sorted(source_user_ids):
        if source_id in used_ids:
            candidate = max_id + 1
            while candidate in used_ids:
                candidate += 1
            user_id_map[source_id] = candidate
            used_ids.add(candidate)
            max_id = max(max_id, candidate)
        else:
            user_id_map[source_id] = source_id
            used_ids.add(source_id)

    return user_id_map
    columns, projects = fetch_rows(source_conn, "project")
    normalized_count = 0
    related_count = 0
    fallback_count = 0
    for project in projects:
        if project.get("created_at") is not None:
            continue
        project_id = project["id"]
        candidates = []
        queries = [
            "SELECT created_at FROM payment WHERE project_id = ? AND created_at IS NOT NULL",
            "SELECT paid_at FROM payment WHERE project_id = ? AND paid_at IS NOT NULL",
            "SELECT created_at FROM professional_project_application WHERE project_id = ? AND created_at IS NOT NULL",
            "SELECT submitted_at FROM project_delivery WHERE project_id = ? AND submitted_at IS NOT NULL",
            "SELECT reviewed_at FROM project_delivery WHERE project_id = ? AND reviewed_at IS NOT NULL",
        ]
        for sql in queries:
            for (value,) in source_conn.execute(sql, (project_id,)).fetchall():
                parsed = parse_timestamp(value)
                if parsed is not None:
                    candidates.append((value, parsed))

        if candidates:
            earliest_value, _ = min(candidates, key=lambda item: item[1])
            project["created_at"] = earliest_value
            related_count += 1
        else:
            project["created_at"] = migration_timestamp
            fallback_count += 1
        normalized_count += 1

    return normalized_count, related_count, fallback_count, projects
def compute_sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_source_hash(path, expected_hash):
    actual_hash = compute_sha256(path)
    if actual_hash.lower() != str(expected_hash).lower():
        fail(
            "Source SHA-256 mismatch: "
            f"expected {expected_hash}, got {actual_hash}"
        )
    return actual_hash


def capture_admin_baseline(conn):
    return conn.execute(
        "SELECT id, name, email, role, password FROM user WHERE id = 1"
    ).fetchone()


def check_email_collisions(source_conn, target_conn):
    source_rows = source_conn.execute(
        "SELECT id, email FROM user"
    ).fetchall()
    target_rows = target_conn.execute(
        "SELECT id, email FROM user"
    ).fetchall()

    source_emails = {
        str(row[1]).strip().lower()
        for row in source_rows
        if row[1] is not None
    }
    target_emails = {
        str(row[1]).strip().lower()
        for row in target_rows
        if row[1] is not None
    }
    collisions = sorted(source_emails & target_emails)
    if collisions:
        fail(
            "Case-insensitive email collision between source and target: "
            + ", ".join(collisions)
        )

    seen = set()
    duplicates = set()
    for row in source_rows:
        if row[1] is None:
            continue
        email = str(row[1]).strip().lower()
        if email in seen:
            duplicates.add(email)
        seen.add(email)
    if duplicates:
        print(
            "WARNING: source contains duplicate email addresses: "
            + ", ".join(sorted(duplicates))
        )


def check_optional_tables(source_conn, target_conn):
    source_tables = table_names(source_conn)
    for table in OPTIONAL_TABLES:
        if table in source_tables and count_rows(source_conn, table) > 0:
            fail(
                f"Optional table {table} contains "
                f"{count_rows(source_conn, table)} source row(s), but "
                "foreign-key remapping is not implemented"
            )


def validate_imported_users(source_conn, target_conn, user_id_map, admin_baseline):
    admin_row = target_conn.execute(
        "SELECT id, name, email, role, password FROM user WHERE id = 1"
    ).fetchone()
    if admin_row != admin_baseline:
        fail("Target admin user (id=1) was not preserved exactly")

    for old_id, new_id in user_id_map.items():
        source_password = source_conn.execute(
            "SELECT password FROM user WHERE id = ?", (old_id,)
        ).fetchone()
        target_password = target_conn.execute(
            "SELECT password FROM user WHERE id = ?", (new_id,)
        ).fetchone()
        if source_password is None or target_password is None:
            fail(f"Missing user row while validating password hash for {old_id} -> {new_id}")
        if source_password[0] != target_password[0]:
            fail(f"Password hash mismatch for imported user {old_id} -> {new_id}")


def validate_imported_payments(source_conn, target_conn, user_id_map):
    cols, source_rows = fetch_rows(source_conn, "payment")
    for source_row in source_rows:
        target_row = target_conn.execute(
            "SELECT " + ", ".join(q(c) for c in cols) + " FROM payment WHERE id = ?",
            (source_row["id"],),
        ).fetchone()
        if target_row is None:
            fail(f"Imported payment {source_row['id']} is missing")
        target_values = dict(zip(cols, target_row))

        if target_values["project_id"] != source_row["project_id"]:
            fail(f"project_id mismatch for payment {source_row['id']}")
        expected_customer_id = user_id_map[source_row["customer_id"]]
        if target_values["customer_id"] != expected_customer_id:
            fail(f"customer_id mismatch for payment {source_row['id']}")

        for column in cols:
            if column in ("project_id", "customer_id"):
                continue
            if target_values[column] != source_row[column]:
                fail(f"{column} mismatch for payment {source_row['id']}")


def normalize_project_timestamps(source_conn, migration_timestamp):
    columns, projects = fetch_rows(source_conn, "project")
    normalized_count = 0
    related_count = 0
    fallback_count = 0
    for project in projects:
        if project.get("created_at") is not None:
            continue
        project_id = project["id"]
        candidates = []
        queries = [
            "SELECT created_at FROM payment WHERE project_id = ? AND created_at IS NOT NULL",
            "SELECT paid_at FROM payment WHERE project_id = ? AND paid_at IS NOT NULL",
            "SELECT created_at FROM professional_project_application WHERE project_id = ? AND created_at IS NOT NULL",
            "SELECT submitted_at FROM project_delivery WHERE project_id = ? AND submitted_at IS NOT NULL",
            "SELECT reviewed_at FROM project_delivery WHERE project_id = ? AND reviewed_at IS NOT NULL",
        ]
        for sql in queries:
            for (value,) in source_conn.execute(sql, (project_id,)).fetchall():
                parsed = parse_timestamp(value)
                if parsed is not None:
                    candidates.append((value, parsed))

        if candidates:
            earliest_value, _ = min(candidates, key=lambda item: item[1])
            project["created_at"] = earliest_value
            related_count += 1
        else:
            project["created_at"] = migration_timestamp
            fallback_count += 1
        normalized_count += 1

    return normalized_count, related_count, fallback_count, projects


def run_migration(source_path, target_path, migration_timestamp, expected_source_sha256=None):
    source_conn = sqlite3.connect(str(source_path))
    target_conn = sqlite3.connect(str(target_path))
    try:
        enable_foreign_keys(source_conn, "source")
        enable_foreign_keys(target_conn, "target")
        verify_schema(source_conn, target_conn)

        # The expected hash, when supplied, is captured by the operator from the
        # immutable source copy immediately after that copy is created. Checking it
        # here detects changes before any target writes, but it cannot by itself
        # prevent concurrent mutation of a live source file.
        if expected_source_sha256 is not None:
            verify_source_hash(source_path, expected_source_sha256)

        source_tables = table_names(source_conn)
        target_tables = table_names(target_conn)

        check_primary_key_collisions(source_conn, target_conn)
        empty_payment_ids = check_payment_uniqueness(source_conn, target_conn)
        check_email_collisions(source_conn, target_conn)
        check_optional_tables(source_conn, target_conn)

        user_id_map = build_user_id_map(source_conn, target_conn)

        normalized_count, related_count, fallback_count, normalized_projects = normalize_project_timestamps(
            source_conn, migration_timestamp
        )
        normalized_project_by_id = {p["id"]: p for p in normalized_projects}

        target_before_counts = {
            t: count_rows(target_conn, t) for t in target_tables
        }
        source_counts = {
            t: count_rows(source_conn, t) for t in source_tables
        }

        admin_baseline = capture_admin_baseline(target_conn)

        target_conn.execute("BEGIN IMMEDIATE")

        inserted_counts = {t: 0 for t in IMPORT_ORDER}

        # user
        src_columns, src_users = fetch_rows(source_conn, "user")
        info = table_info(source_conn, "user")
        for row in src_users:
            validate_row("user", info, row)
            new_row = dict(row)
            new_row["id"] = user_id_map[row["id"]]
            target_conn.execute(
                "INSERT INTO user (" + ", ".join(q(c) for c in src_columns) + ") "
                "VALUES (" + ", ".join("?" for _ in src_columns) + ")",
                [new_row[c] for c in src_columns],
            )
            inserted_counts["user"] += 1

        validate_imported_users(source_conn, target_conn, user_id_map, admin_baseline)

        if "customer_profile" in source_tables and count_rows(source_conn, "customer_profile") > 0:
            cols, rows = fetch_rows(source_conn, "customer_profile")
            info = table_info(source_conn, "customer_profile")
            for row in rows:
                validate_row("customer_profile", info, row)
                new_row = dict(row)
                new_row["user_id"] = user_id_map[row["user_id"]]
                target_conn.execute(
                    "INSERT INTO customer_profile (" + ", ".join(q(c) for c in cols) + ") "
                    "VALUES (" + ", ".join("?" for _ in cols) + ")",
                    [new_row[c] for c in cols],
                )
                inserted_counts["customer_profile"] += 1

        # professional_profile
        if "professional_profile" in source_tables and count_rows(source_conn, "professional_profile") > 0:
            cols, rows = fetch_rows(source_conn, "professional_profile")
            info = table_info(source_conn, "professional_profile")
            for row in rows:
                validate_row("professional_profile", info, row)
                new_row = dict(row)
                new_row["user_id"] = user_id_map[row["user_id"]]
                target_conn.execute(
                    "INSERT INTO professional_profile (" + ", ".join(q(c) for c in cols) + ") "
                    "VALUES (" + ", ".join("?" for _ in cols) + ")",
                    [new_row[c] for c in cols],
                )
                inserted_counts["professional_profile"] += 1

        # business
        if "business" in source_tables and count_rows(source_conn, "business") > 0:
            cols, rows = fetch_rows(source_conn, "business")
            info = table_info(source_conn, "business")
            for row in rows:
                validate_row("business", info, row)
                new_row = dict(row)
                new_row["customer_id"] = user_id_map[row["customer_id"]]
                target_conn.execute(
                    "INSERT INTO business (" + ", ".join(q(c) for c in cols) + ") "
                    "VALUES (" + ", ".join("?" for _ in cols) + ")",
                    [new_row[c] for c in cols],
                )
                inserted_counts["business"] += 1
        # project
        if "project" in source_tables and count_rows(source_conn, "project") > 0:
            cols, rows = fetch_rows(source_conn, "project")
            info = table_info(source_conn, "project")
            for row in rows:
                validate_row("project", info, row)
                new_row = dict(row)
                new_row["customer_id"] = user_id_map[row["customer_id"]]
                if row["id"] in normalized_project_by_id:
                    new_row["created_at"] = normalized_project_by_id[row["id"]]["created_at"]
                target_conn.execute(
                    "INSERT INTO project (" + ", ".join(q(c) for c in cols) + ") "
                    "VALUES (" + ", ".join("?" for _ in cols) + ")",
                    [new_row[c] for c in cols],
                )
                inserted_counts["project"] += 1

        # professional_project_application
        if "professional_project_application" in source_tables and count_rows(source_conn, "professional_project_application") > 0:
            cols, rows = fetch_rows(source_conn, "professional_project_application")
            info = table_info(source_conn, "professional_project_application")
            for row in rows:
                validate_row("professional_project_application", info, row)
                new_row = dict(row)
                new_row["professional_id"] = user_id_map[row["professional_id"]]
                target_conn.execute(
                    "INSERT INTO professional_project_application (" + ", ".join(q(c) for c in cols) + ") "
                    "VALUES (" + ", ".join("?" for _ in cols) + ")",
                    [new_row[c] for c in cols],
                )
                inserted_counts["professional_project_application"] += 1

        # project_delivery
        if "project_delivery" in source_tables and count_rows(source_conn, "project_delivery") > 0:
            cols, rows = fetch_rows(source_conn, "project_delivery")
            info = table_info(source_conn, "project_delivery")
            for row in rows:
                validate_row("project_delivery", info, row)
                new_row = dict(row)
                new_row["professional_id"] = user_id_map[row["professional_id"]]
                target_conn.execute(
                    "INSERT INTO project_delivery (" + ", ".join(q(c) for c in cols) + ") "
                    "VALUES (" + ", ".join("?" for _ in cols) + ")",
                    [new_row[c] for c in cols],
                )
                inserted_counts["project_delivery"] += 1

        # payment
        if "payment" in source_tables and count_rows(source_conn, "payment") > 0:
            cols, rows = fetch_rows(source_conn, "payment")
            info = table_info(source_conn, "payment")
            for row in rows:
                validate_row("payment", info, row)
                new_row = dict(row)
                new_row["customer_id"] = user_id_map[row["customer_id"]]
                target_conn.execute(
                    "INSERT INTO payment (" + ", ".join(q(c) for c in cols) + ") "
                    "VALUES (" + ", ".join("?" for _ in cols) + ")",
                    [new_row[c] for c in cols],
                )
                inserted_counts["payment"] += 1

        validate_imported_payments(source_conn, target_conn, user_id_map)

        for table in ["chat_message", "invoice", "notification"]:
            if table in source_tables and table in target_tables and count_rows(source_conn, table) > 0:
                cols, rows = fetch_rows(source_conn, table)
                info = table_info(source_conn, table)
                for row in rows:
                    validate_row(table, info, row)
                    target_conn.execute(
                        "INSERT INTO " + q(table) + " (" + ", ".join(q(c) for c in cols) + ") "
                        "VALUES (" + ", ".join("?" for _ in cols) + ")",
                        [row[c] for c in cols],
                    )
                    inserted_counts[table] += 1
        # Validate foreign keys before commit.
        fk_issues = target_conn.execute("PRAGMA foreign_key_check").fetchall()
        if fk_issues:
            fail(f"Foreign-key check failed: {fk_issues}")

        # Also validate user id 1 preserved.
        admin_row = target_conn.execute("SELECT id, role FROM user WHERE id = 1").fetchone()
        if not admin_row or admin_row[1] != "admin":
            fail("Target admin user with id 1 and role 'admin' was not preserved")

        target_conn.commit()

        target_after_counts = {
            t: count_rows(target_conn, t) for t in target_tables
        }

        summary = {
            "user_id_map": user_id_map,
            "normalized_projects": normalized_count,
            "normalized_related": related_count,
            "normalized_fallback": fallback_count,
            "empty_payment_ids": empty_payment_ids,
            "inserted_counts": inserted_counts,
            "source_counts": source_counts,
            "target_before_counts": target_before_counts,
            "target_after_counts": target_after_counts,
        }
        return summary
    except Exception as exc:
        try:
            target_conn.rollback()
        except Exception:
            pass
        if isinstance(exc, RuntimeError):
            raise
        raise RuntimeError(str(exc)) from exc
    finally:
        try:
            source_conn.close()
        except Exception:
            pass
        try:
            target_conn.close()
        except Exception:
            pass
def parse_args():
    parser = argparse.ArgumentParser(
        description="Recover AgencyOS source data into a disposable target copy."
    )
    parser.add_argument("--source-copy", required=True, help="Path to disposable source copy")
    parser.add_argument("--target-copy", required=True, help="Path to disposable target copy")
    parser.add_argument(
        "--confirm-disposable-target",
        action="store_true",
        required=True,
        help="Explicit confirmation that target is disposable",
    )
    parser.add_argument(
        "--expected-source-sha256",
        default=None,
        help="Expected SHA-256 of the immutable source copy",
    )
    parser.add_argument(
        "--migration-timestamp",
        default=DEFAULT_MIGRATION_TIMESTAMP,
        help="Fallback timestamp for projects without related timestamps",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    source_path = resolve_path(args.source_copy)
    target_path = resolve_path(args.target_copy)

    if not source_path.is_file():
        print("ERROR: source copy does not exist or is not a file")
        return 1
    if not target_path.is_file():
        print("ERROR: target copy does not exist or is not a file")
        return 1

    protected, reason = is_protected(source_path)
    if protected:
        print(f"ERROR: source path is {reason}; refusing to run")
        return 1
    protected, reason = is_protected(target_path)
    if protected:
        print(f"ERROR: target path is {reason}; refusing to run")
        return 1
    if source_path == target_path:
        print("ERROR: source and target paths resolve to the same file")
        return 1

    try:
        summary = run_migration(
            source_path,
            target_path,
            args.migration_timestamp,
            args.expected_source_sha256,
        )
    except Exception as exc:
        print(f"ERROR: recovery failed and target was rolled back: {exc}")
        return 1

    print("Recovery completed successfully.")
    print("User ID mapping:")
    for old_id, new_id in sorted(summary["user_id_map"].items()):
        print(f"  {old_id} -> {new_id}")
    print(
        "Normalized project created_at values: "
        f"{summary['normalized_projects']} "
        f"(related_timestamp={summary['normalized_related']}, "
        f"migration_timestamp={summary['normalized_fallback']})"
    )
    print(f"Empty payment IDs preserved: {summary['empty_payment_ids']}")
    print("Inserted counts:")
    for table in IMPORT_ORDER:
        print(f"  {table}: {summary['inserted_counts'].get(table, 0)}")
    print("Source counts:")
    for table, value in sorted(summary["source_counts"].items()):
        print(f"  {table}: {value}")
    print("Target counts before:")
    for table, value in sorted(summary["target_before_counts"].items()):
        print(f"  {table}: {value}")
    print("Target counts after:")
    for table, value in sorted(summary["target_after_counts"].items()):
        print(f"  {table}: {value}")
    print("Foreign-key check: 0 issues")
    print("Target admin id 1: preserved")
    print("Payment uniqueness preflight: passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
