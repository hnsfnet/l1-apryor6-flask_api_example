from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_restx import Api

db = SQLAlchemy()

API_TITLE = "Flaskerific API"
API_VERSION = "0.1.0"


def create_app(env=None):
    from app.config import config_by_name
    from app.routes import register_routes
    from app.shared.errors import register_error_handlers

    app = Flask(__name__)
    app.config.from_object(config_by_name[env or "test"])
    # Keep our own 404 message clean; don't let flask-restx append route hints.
    app.config["ERROR_404_HELP"] = False
    api = Api(app, title=API_TITLE, version=API_VERSION)

    register_routes(api, app)
    register_error_handlers(api)
    db.init_app(app)

    @app.route("/health")
    def health():
        return jsonify(
            {"status": "ok", "service": API_TITLE, "version": API_VERSION}
        )

    return app
