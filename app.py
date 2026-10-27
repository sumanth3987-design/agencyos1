import os

from app import create_app
from app.config import resolve_flask_env


config_name = resolve_flask_env()
app = create_app(config_name)

if __name__ == "__main__":

    debug = (
        config_name == "development"
        and bool(app.config.get("DEBUG", False))
    )

    app.run(
        debug=debug
    )
