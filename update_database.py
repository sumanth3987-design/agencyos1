from app import app, db
from sqlalchemy import text, inspect


def column_exists(table_name, column_name):
    inspector = inspect(db.engine)

    if table_name not in inspector.get_table_names():
        return False

    columns = inspector.get_columns(table_name)

    return any(column["name"] == column_name for column in columns)


with app.app_context():

    try:
        # Create any new tables that do not already exist
        db.create_all()

        print("Checking database...")

        # ---------------------------------------------------------
        # PROJECT TABLE
        # ---------------------------------------------------------

        if not column_exists("project", "revision_comment"):
            db.session.execute(
                text(
                    "ALTER TABLE project ADD COLUMN revision_comment TEXT"
                )
            )
            print("Added: project.revision_comment")
        else:
            print("Already exists: project.revision_comment")

        # ---------------------------------------------------------
        # PROFESSIONAL PROFILE TABLE
        # ---------------------------------------------------------

        professional_columns = {
            "phone": "TEXT",
            "location": "TEXT",
            "skills": "TEXT",
            "technologies": "TEXT",
            "skill_level": "TEXT",
            "project_types": "TEXT",
            "github": "TEXT",
            "linkedin": "TEXT",
            "education": "TEXT",
            "certifications": "TEXT",
            "work_experience": "TEXT",
            "availability": "TEXT",
            "current_workload": "TEXT",
            "verification_notes": "TEXT",
            "profile_completed": "BOOLEAN DEFAULT 0",
            "updated_at": "DATETIME"
        }

        for column_name, column_type in professional_columns.items():

            if not column_exists(
                "professional_profile",
                column_name
            ):

                db.session.execute(
                    text(
                        f"""
                        ALTER TABLE professional_profile
                        ADD COLUMN {column_name} {column_type}
                        """
                    )
                )

                print(
                    f"Added: professional_profile.{column_name}"
                )

            else:

                print(
                    f"Already exists: professional_profile.{column_name}"
                )

        # ---------------------------------------------------------
        # CUSTOMER PROFILE TABLE
        # ---------------------------------------------------------

        print("Checking customer_profile table...")

        if "customer_profile" in inspect(db.engine).get_table_names():

            print("customer_profile table exists")

        else:

            print(
                "customer_profile table was not created."
            )

        # Save all changes
        db.session.commit()

        print()
        print("========================================")
        print("DATABASE MIGRATION COMPLETED SUCCESSFULLY")
        print("========================================")

    except Exception as error:

        db.session.rollback()

        print()
        print("========================================")
        print("DATABASE MIGRATION ERROR")
        print("========================================")
        print(error)