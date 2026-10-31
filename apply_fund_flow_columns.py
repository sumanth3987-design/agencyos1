import sqlite3
import os

DB_PATH = os.path.join("instance", "agencyos.db")

def add_column_if_missing(cursor, table, column_def):
    col_name = column_def.split()[0]
    cursor.execute(f"PRAGMA table_info({table});")
    existing_cols = [col[1] for col in cursor.fetchall()]
    if col_name not in existing_cols:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column_def};")
        print(f"Added {col_name} to {table}")
    else:
        print(f"{col_name} already exists in {table}")

def main():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("Running safe migration on instance/agencyos.db...")

    # 1. Add Payout details to professional_profile
    add_column_if_missing(cursor, "professional_profile", "upi_id TEXT")
    add_column_if_missing(cursor, "professional_profile", "bank_account_number TEXT")
    add_column_if_missing(cursor, "professional_profile", "bank_ifsc TEXT")
    add_column_if_missing(cursor, "professional_profile", "pan_number TEXT")

    # 2. Add Payout tracking to invoice
    add_column_if_missing(cursor, "invoice", "payout_status TEXT NOT NULL DEFAULT 'Pending Approval'")
    add_column_if_missing(cursor, "invoice", "payout_utr TEXT")
    add_column_if_missing(cursor, "invoice", "payout_paid_at DATETIME")

    conn.commit()
    conn.close()
    print("Migration completed successfully! Database is up to date.")

if __name__ == "__main__":
    main()
