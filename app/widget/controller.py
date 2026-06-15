from flask import request
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource, fields as rx_fields
from flask.wrappers import Response
from typing import List

from .schema import WidgetSchema
from .service import WidgetService
from .model import Widget
from .interface import WidgetInterface

api = Namespace("Widget", description="Single namespace, single entity")  # noqa

widget_item = api.model(
    "WidgetInput",
    {
        "name": rx_fields.String(required=True, description="Widget name"),
        "purpose": rx_fields.String(required=True, description="Widget purpose"),
    },
)

widget_entity = api.model(
    "Widget",
    {
        "widgetId": rx_fields.Integer(description="Widget database ID"),
        "name": rx_fields.String(),
        "purpose": rx_fields.String(),
    },
)

widget_create_failure = api.model(
    "WidgetBulkCreateFailure",
    {
        "index": rx_fields.Integer(description="Position in the submitted list"),
        "item": rx_fields.Raw(description="The submitted payload that was rejected"),
        "error": rx_fields.String(description="Why the item was rejected"),
    },
)

widget_bulk_create_request = api.model(
    "WidgetBulkCreateRequest",
    {
        "items": rx_fields.List(
            rx_fields.Nested(widget_item),
            required=True,
            description="Widgets to create",
        )
    },
)

widget_bulk_create_response = api.model(
    "WidgetBulkCreateResponse",
    {
        "success_count": rx_fields.Integer(description="Number of widgets created"),
        "failure_count": rx_fields.Integer(description="Number of rejected items"),
        "succeeded": rx_fields.List(rx_fields.Nested(widget_entity)),
        "failed": rx_fields.List(rx_fields.Nested(widget_create_failure)),
    },
)

widget_bulk_delete_request = api.model(
    "WidgetBulkDeleteRequest",
    {
        "ids": rx_fields.List(
            rx_fields.Integer,
            required=True,
            description="Widget IDs to delete",
        )
    },
)

widget_bulk_delete_response = api.model(
    "WidgetBulkDeleteResponse",
    {
        "success_count": rx_fields.Integer(description="Number of widgets deleted"),
        "failure_count": rx_fields.Integer(description="Number of ids not found"),
        "requested": rx_fields.List(rx_fields.Integer, description="Ids as received"),
        "deleted": rx_fields.List(rx_fields.Integer),
        "not_found": rx_fields.List(rx_fields.Integer),
    },
)


@api.route("/")
class WidgetResource(Resource):
    """Widgets"""

    @responds(schema=WidgetSchema, many=True)
    def get(self) -> List[Widget]:
        """Get all Widgets"""

        return WidgetService.get_all()

    @accepts(schema=WidgetSchema, api=api)
    @responds(schema=WidgetSchema)
    def post(self) -> Widget:
        """Create a Single Widget"""

        return WidgetService.create(request.parsed_obj)


@api.route("/<int:widgetId>")
@api.param("widgetId", "Widget database ID")
class WidgetIdResource(Resource):
    @responds(schema=WidgetSchema)
    def get(self, widgetId: int) -> Widget:
        """Get Single Widget"""

        return WidgetService.get_by_id(widgetId)

    def delete(self, widgetId: int) -> Response:
        """Delete Single Widget"""
        from flask import jsonify

        id = WidgetService.delete_by_id(widgetId)
        return jsonify(dict(status="Success", id=id))

    @accepts(schema=WidgetSchema, api=api)
    @responds(schema=WidgetSchema)
    def put(self, widgetId: int) -> Widget:
        """Update Single Widget"""

        changes: WidgetInterface = request.parsed_obj
        Widget = WidgetService.get_by_id(widgetId)
        return WidgetService.update(Widget, changes)


@api.route("/bulk")
class WidgetBulkResource(Resource):
    """Create or delete many Widgets in a single request"""

    @api.expect(widget_bulk_create_request)
    @api.marshal_with(widget_bulk_create_response)
    def post(self):
        """Create a batch of Widgets

        Send ``{"items": [{"name": ..., "purpose": ...}, ...]}``. Valid items
        are created even if others are rejected; the response reports how many
        succeeded, how many failed and exactly which items failed and why.
        """
        payload = request.get_json(silent=True) or {}
        result = WidgetService.create_bulk(payload.get("items", []))
        return {
            "success_count": result["success_count"],
            "failure_count": result["failure_count"],
            "succeeded": WidgetSchema(many=True).dump(result["succeeded"]),
            "failed": result["failed"],
        }

    @api.expect(widget_bulk_delete_request)
    @api.marshal_with(widget_bulk_delete_response)
    def delete(self):
        """Delete a batch of Widgets by id

        Send ``{"ids": [1, 2, 3]}``. Ids that do not exist (or were already
        deleted earlier in the same request) are returned under ``not_found``
        instead of failing the whole call.
        """
        payload = request.get_json(silent=True) or {}
        return WidgetService.delete_bulk(payload.get("ids", []))
