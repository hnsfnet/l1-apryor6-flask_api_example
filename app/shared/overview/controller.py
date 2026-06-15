from flask_restx import Namespace, Resource
from flask import jsonify

from app.shared.query.service import QueryService

api = Namespace("Overview", description="System-wide resource summary")


def _get_resource_descriptors():
    """Lazily import models to avoid circular import issues."""
    from app.widget.model import Widget
    from app.fizz.fizzbar.model import Fizzbar
    from app.fizz.fizzbaz.model import Fizzbaz
    from app.other_api.doodad.model import Doodad
    from app.other_api.whatsit.model import Whatsit

    return [
        {"name": "widget", "model": Widget, "id_col": "widget_id"},
        {"name": "fizzbar", "model": Fizzbar, "id_col": "fizzbar_id"},
        {"name": "fizzbaz", "model": Fizzbaz, "id_col": "fizzbaz_id"},
        {"name": "doodad", "model": Doodad, "id_col": "doodad_id"},
        {"name": "whatsit", "model": Whatsit, "id_col": "whatsit_id"},
    ]


@api.route("/")
class OverviewResource(Resource):
    """Resource overview for all registered modules."""

    def get(self):
        """Get a summary of all resources: counts and latest record."""
        resources = _get_resource_descriptors()
        summary = QueryService.get_resource_summary(resources)
        return jsonify({"resources": summary})
