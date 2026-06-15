from flask import jsonify, request
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource
from flask.wrappers import Response
from typing import List

from .schema import WidgetSchema
from .service import WidgetService
from .model import Widget
from .interface import WidgetInterface

api = Namespace("Widget", description="Single namespace, single entity")  # noqa


@api.route("/")
class WidgetResource(Resource):
    """Widgets"""

    @responds(schema=WidgetSchema, many=True)
    def get(self) -> List[Widget]:
        """Get all Widgets"""

        return WidgetService.get_all()

    @accepts(schema=WidgetSchema, api=api)
    @responds(schema=WidgetSchema)
    @api.response(400, "Request body failed validation")
    def post(self) -> Widget:
        """Create a Single Widget"""

        return WidgetService.create(request.parsed_obj)


@api.route("/<int:widgetId>")
@api.param("widgetId", "Widget database ID")
class WidgetIdResource(Resource):
    @responds(schema=WidgetSchema)
    @api.response(404, "Widget not found")
    def get(self, widgetId: int) -> Widget:
        """Get Single Widget"""

        return WidgetService.get_by_id(widgetId)

    @api.response(200, "Widget deleted")
    @api.response(404, "Widget not found")
    def delete(self, widgetId: int) -> Response:
        """Delete Single Widget"""

        id = WidgetService.delete_by_id(widgetId)
        return jsonify(dict(status="Success", id=id))

    @accepts(schema=WidgetSchema, api=api)
    @responds(schema=WidgetSchema)
    @api.response(400, "Request body failed validation")
    @api.response(404, "Widget not found")
    def put(self, widgetId: int) -> Widget:
        """Update Single Widget"""

        changes: WidgetInterface = request.parsed_obj
        widget = WidgetService.get_by_id(widgetId)
        return WidgetService.update(widget, changes)
