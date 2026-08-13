from flask import Flask

from app.config import get_config
from app.extensions import db
from app.logging_setup import configure_logging


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    configure_logging(app)
    db.init_app(app)

    from app import models  # noqa: F401  ensure models are registered
    from app.routes import register_blueprints

    register_blueprints(app)

    return app
