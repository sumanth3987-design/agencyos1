import sqlite3
import os


# =========================================================
# DATABASE PATH
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DB_PATH = os.path.join(
    BASE_DIR,
    "instance",
    "agencyos.db"
)


# =========================================================
# CHECK DATABASE
# =========================================================

if not os.path.exists(DB_PATH):

    raise FileNotFoundError(
        f"Database not found:\n{DB_PATH}"
    )


# =========================================================
# CONNECT TO SQLITE
# =========================================================

connection = sqlite3.connect(DB_PATH)

cursor = connection.cursor()


try:

    print()
    print("Connected to:")
    print(DB_PATH)
    print()


    # =====================================================
    # CHECK USER TABLE
    # =====================================================

    cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name = 'user'
        """
    )

    if not cursor.fetchone():

        raise RuntimeError(
            "The 'user' table was not found."
        )


    # =====================================================
    # SHOW USERS BEFORE MIGRATION
    # =====================================================

    cursor.execute(
        """
        SELECT
            id,
            name,
            email,
            role
        FROM user
        ORDER BY id
        """
    )

    users_before = cursor.fetchall()

    print("Users before migration:")

    for user in users_before:

        print(user)

    print()


    # =====================================================
    # START TRANSACTION
    # =====================================================

    cursor.execute(
        "PRAGMA foreign_keys = OFF"
    )


    # =====================================================
    # CREATE NEW USER TABLE
    #
    # IMPORTANT:
    # email is NOT UNIQUE.
    # =====================================================

    cursor.execute(
        """
        CREATE TABLE user_new (

            id INTEGER NOT NULL PRIMARY KEY,

            name VARCHAR(100) NOT NULL,

            email VARCHAR(120) NOT NULL,

            password VARCHAR(255) NOT NULL,

            role VARCHAR(30),

            created_at DATETIME
                DEFAULT CURRENT_TIMESTAMP

        )
        """
    )


    # =====================================================
    # COPY EXISTING USERS
    # =====================================================

    cursor.execute(
        """
        INSERT INTO user_new (
            id,
            name,
            email,
            password,
            role,
            created_at
        )

        SELECT
            id,
            name,
            email,
            password,
            role,
            created_at

        FROM user
        """
    )


    # =====================================================
    # DELETE OLD TABLE
    # =====================================================

    cursor.execute(
        "DROP TABLE user"
    )


    # =====================================================
    # RENAME NEW TABLE
    # =====================================================

    cursor.execute(
        "ALTER TABLE user_new RENAME TO user"
    )


    # =====================================================
    # RESTORE FOREIGN KEYS
    # =====================================================

    cursor.execute(
        "PRAGMA foreign_keys = ON"
    )


    # =====================================================
    # COMMIT
    # =====================================================

    connection.commit()


    # =====================================================
    # VERIFY USERS
    # =====================================================

    cursor.execute(
        """
        SELECT
            id,
            name,
            email,
            role
        FROM user
        ORDER BY id
        """
    )

    users_after = cursor.fetchall()

    print("Users after migration:")

    for user in users_after:

        print(user)

    print()


    # =====================================================
    # VERIFY EMAIL IS NOT UNIQUE
    # =====================================================

    cursor.execute(
        "PRAGMA index_list('user')"
    )

    indexes = cursor.fetchall()

    unique_email_found = False

    for index in indexes:

        index_name = index[1]
        is_unique = index[2]

        cursor.execute(
            f'PRAGMA index_info("{index_name}")'
        )

        columns = cursor.fetchall()

        column_names = [
            column[2]
            for column in columns
        ]

        if (
            is_unique == 1
            and column_names == ["email"]
        ):

            unique_email_found = True


    if unique_email_found:

        raise RuntimeError(
            "Migration failed: "
            "email is still UNIQUE."
        )


    # =====================================================
    # SUCCESS
    # =====================================================

    print(
        "SUCCESS: email is no longer UNIQUE."
    )

    print(
        "Existing users have been preserved."
    )

    print()

    print(
        "Database migration completed successfully."
    )

    print()


except Exception as error:

    connection.rollback()

    print()
    print("MIGRATION FAILED:")
    print(error)
    print()

    raise


finally:

    connection.close()