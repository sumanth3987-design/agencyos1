import os
import sys

from app import create_app
from app.config import resolve_flask_env
from app.extensions import db
from app.models import User
from werkzeug.security import generate_password_hash

config_name = resolve_flask_env()
app = create_app(config_name)

admin_email = os.getenv("ADMIN_EMAIL", "").strip()
admin_password = os.getenv("ADMIN_PASSWORD", "")

if not admin_email or not admin_password:
    print(
        "ADMIN_EMAIL and ADMIN_PASSWORD environment variables are required "
        "to create or update an administrator account."
    )
    sys.exit(1)

with app.app_context():
    admin = User.query.filter_by(
        email=admin_email
    ).first()

    if admin:
        admin.name = os.getenv("ADMIN_NAME", "AgencyOS Admin")
        admin.password = generate_password_hash(admin_password)
        admin.role = "admin"

        db.session.commit()

        print("ADMIN UPDATED SUCCESSFULLY")
    else:
        admin = User(
            name=os.getenv("ADMIN_NAME", "AgencyOS Admin"),
            email=admin_email,
            password=generate_password_hash(admin_password),
            role="admin"
        )

        db.session.add(admin)
        db.session.commit()

        print("ADMIN CREATED SUCCESSFULLY")
