import os

from app import create_app
from app.config import resolve_flask_env
from app.extensions import db

env = resolve_flask_env()
app = create_app(env)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    port = int(os.getenv("PORT", 5000))
    debug = (
        env == "development"
        and bool(app.config.get("DEBUG", False))
    )
    app.run(host="0.0.0.0", port=port, debug=debug)
