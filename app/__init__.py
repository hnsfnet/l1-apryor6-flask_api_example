from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_restx import Api

db = SQLAlchemy()


def create_app(env=None):
    from app.config import config_by_name
    from app.routes import register_routes

    app = Flask(__name__)
    app.config.from_object(config_by_name[env or "test"])
    api = Api(app, title="Flaskerific API", version="0.1.0")

    register_routes(api, app)
    db.init_app(app)

    @app.route("/health")
    def health():
        from sqlalchemy import text
        from app.shared.overview.service import OverviewService

        # Lightweight DB connectivity probe so env issues are visible here
        # instead of only surfacing deep in request logs.
        database = "connected"
        try:
            db.session.execute(text("SELECT 1"))
        except Exception:
            db.session.rollback()
            database = "disconnected"

        return jsonify(
            {
                "status": "healthy",
                "database": database,
                "modules": OverviewService.module_names(),
            }
        )

    return app
