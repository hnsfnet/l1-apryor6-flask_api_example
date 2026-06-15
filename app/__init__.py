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
        from app.shared.query.service import QueryService

        db_ok = QueryService.check_db_connectivity()

        # Check which modules are registered by inspecting blueprints
        registered_modules = []
        for bp_name in app.blueprints:
            registered_modules.append(bp_name)

        # Also check the restx namespaces
        registered_namespaces = []
        for ns in api.namespaces:
            registered_namespaces.append(ns.name if hasattr(ns, 'name') else str(ns))

        status = "healthy" if db_ok else "degraded"

        return jsonify({
            "status": status,
            "database": "connected" if db_ok else "unavailable",
            "modules": registered_modules,
            "namespaces": registered_namespaces,
        })

    return app
