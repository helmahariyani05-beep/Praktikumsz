import os

from flask import Flask

from app.config import Config


def create_app(config_class=Config):
    """Create and configure the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    app.config["DATABASE"] = os.environ.get(
        "LAB_EQUIPMENT_DATABASE",
        os.path.join(app.instance_path, "lab_equipment.db"),
    )

    os.makedirs(app.instance_path, exist_ok=True)

    # Keep JSON field order predictable in responses.
    app.json.sort_keys = app.config["JSON_SORT_KEYS"]

    return app
