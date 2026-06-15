from flask import request
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource
from flask.wrappers import Response
from typing import List

from app.shared.errors import NotFoundException, ValidationError, error_response, register_error_models
from .schema import WidgetSchema
from .service import WidgetService
from .model import Widget
from .interface import WidgetInterface

api = Namespace("Widget", description="Single namespace, single entity")  # noqa
error_model = register_error_models(api)


@api.route("/")
class WidgetResource(Resource):
    """Widgets"""

    @responds(schema=WidgetSchema, many=True)
    def get(self) -> List[Widget]:
        """Get all Widgets"""

        return WidgetService.get_all()

    @accepts(schema=WidgetSchema, api=api)
    @responds(schema=WidgetSchema)
    @api.response(400, "Validation error", error_model)
    def post(self) -> Widget:
        """Create a Single Widget

        Requires ``name`` and ``purpose`` to be non-empty strings.
        """

        _validate_widget_payload(request.parsed_obj)
        return WidgetService.create(request.parsed_obj)


@api.route("/<int:widgetId>")
@api.param("widgetId", "Widget database ID")
class WidgetIdResource(Resource):
    @responds(schema=WidgetSchema)
    @api.response(404, "Widget not found", error_model)
    def get(self, widgetId: int) -> Widget:
        """Get Single Widget"""

        widget = WidgetService.get_by_id(widgetId)
        if not widget:
            raise NotFoundException("Widget", widgetId)
        return widget

    @api.response(200, "Success")
    @api.response(404, "Widget not found", error_model)
    def delete(self, widgetId: int) -> Response:
        """Delete Single Widget"""
        from flask import jsonify

        widget = WidgetService.get_by_id(widgetId)
        if not widget:
            raise NotFoundException("Widget", widgetId)
        WidgetService.delete_by_id(widgetId)
        return jsonify(dict(status="Success", id=[widgetId]))

    @accepts(schema=WidgetSchema, api=api)
    @responds(schema=WidgetSchema)
    @api.response(400, "Validation error", error_model)
    @api.response(404, "Widget not found", error_model)
    def put(self, widgetId: int) -> Widget:
        """Update Single Widget"""

        changes: WidgetInterface = request.parsed_obj
        widget = WidgetService.get_by_id(widgetId)
        if not widget:
            raise NotFoundException("Widget", widgetId)
        return WidgetService.update(widget, changes)


def _validate_widget_payload(data: dict) -> None:
    """Raise ValidationError if required fields are missing or empty."""
    errors = {}
    for field in ("name", "purpose"):
        value = data.get(field)
        if value is None or (isinstance(value, str) and value.strip() == ""):
            errors[field] = f"Field '{field}' is required and must not be empty."
    if errors:
        raise ValidationError(message="Invalid request body", details=errors)
