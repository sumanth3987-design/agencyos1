import sqlite3
import os

DB_PATH = os.path.join("instance", "agencyos.db")

def add_col_if_missing(cursor, table, col_def):
    col_name = col_def.split()[0]
    cursor.execute(f"PRAGMA table_info({table});")
    existing_cols = [c[1] for c in cursor.fetchall()]
    if col_name not in existing_cols:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_def};")
        print(f"✅ Added {col_name} to {table}")
    else:
        print(f"ℹ️ {col_name} already exists in {table}")

def main():
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    print("Fixing user table schema in instance/agencyos.db...")

    # Add missing authentication security columns to user table
    add_col_if_missing(cursor, "user", "email_verified_at DATETIME")
    add_col_if_missing(cursor, "user", "session_version INTEGER NOT NULL DEFAULT 0")

    conn.commit()
    conn.close()
    print("🎉 Database schema synchronized successfully!")

if __name__ == "__main__":
    main()