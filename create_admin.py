from app import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    admin = User.query.filter_by(
        email="admin@agencyos.com"
    ).first()

    if admin:
        admin.name = "AgencyOS Admin"
        admin.password = generate_password_hash("Admin@12345")
        admin.role = "admin"

        db.session.commit()

        print("ADMIN UPDATED SUCCESSFULLY")

    else:
        admin = User(
            name="AgencyOS Admin",
            email="admin@agencyos.com",
            password=generate_password_hash("Admin@12345"),
            role="admin"
        )

        db.session.add(admin)
        db.session.commit()

        print("ADMIN CREATED SUCCESSFULLY")