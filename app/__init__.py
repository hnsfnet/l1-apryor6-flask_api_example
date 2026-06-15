from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_restx import Api
from sqlalchemy import text

db = SQLAlchemy()


def create_app(env=None):
    from app.config import config_by_name
    from app.routes import register_routes
    from app.shared.errors import register_error_handlers

    app = Flask(__name__)
    app.config.from_object(config_by_name[env or "test"])
    api = Api(app, title="Flaskerific API", version="0.1.0")

    register_routes(api, app)
    db.init_app(app)
    register_error_handlers(app)

    @app.route("/health")
    def health():
        """Return structured health information.

        Response includes service status and database connectivity so that
        external monitoring tools can consume it directly.
        """
        db_ok = True
        try:
            db.session.execute(text("SELECT 1"))
        except Exception:
            db_ok = False

        status = "healthy" if db_ok else "degraded"
        code = 200 if db_ok else 503
        return jsonify({
            "status": status,
            "version": "0.1.0",
            "checks": {
                "database": "ok" if db_ok else "failed",
            },
        }), code

    return app
