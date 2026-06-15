from flask import request, jsonify
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource, fields as restx_fields
from flask.wrappers import Response
from typing import List

from .schema import WidgetSchema
from .service import WidgetService
from .model import Widget
from .interface import WidgetInterface

api = Namespace("Widget", description="Single namespace, single entity")  # noqa

# ---------------------------------------------------------------------------
# Swagger models for batch operations
# ---------------------------------------------------------------------------
_widget_create_item = api.model(
    "WidgetCreateItem",
    {
        "name": restx_fields.String(required=True, description="Widget name"),
        "purpose": restx_fields.String(description="Widget purpose"),
    },
)

_widget_batch_create_request = api.model(
    "WidgetBatchCreateRequest",
    {
        "items": restx_fields.List(
            restx_fields.Nested(_widget_create_item),
            description="List of widgets to create",
        )
    },
)

_widget_batch_delete_request = api.model(
    "WidgetBatchDeleteRequest",
    {
        "ids": restx_fields.List(
            restx_fields.Integer,
            description="List of widget IDs to delete",
        )
    },
)

_batch_error_item = api.model(
    "WidgetBatchErrorItem",
    {
        "index": restx_fields.Integer(description="Index in the original request"),
        "error": restx_fields.String(description="Error message"),
    },
)

_widget_batch_create_response = api.model(
    "WidgetBatchCreateResponse",
    {
        "total": restx_fields.Integer(description="Total items requested"),
        "succeeded": restx_fields.Integer(description="Successfully created count"),
        "failed": restx_fields.Integer(description="Failed count"),
        "successful_items": restx_fields.List(
            restx_fields.Nested(
                api.model(
                    "WidgetSummary",
                    {
                        "widgetId": restx_fields.Integer(attribute="widget_id"),
                        "name": restx_fields.String,
                        "purpose": restx_fields.String,
                    },
                )
            )
        ),
        "failed_items": restx_fields.List(restx_fields.Nested(_batch_error_item)),
    },
)

_batch_delete_error_item = api.model(
    "WidgetBatchDeleteErrorItem",
    {
        "id": restx_fields.Integer(description="ID that could not be deleted"),
        "error": restx_fields.String(description="Error message"),
    },
)

_widget_batch_delete_response = api.model(
    "WidgetBatchDeleteResponse",
    {
        "total": restx_fields.Integer(description="Total IDs requested"),
        "succeeded": restx_fields.Integer(description="Successfully deleted count"),
        "failed": restx_fields.Integer(description="Failed count"),
        "successful_ids": restx_fields.List(restx_fields.Integer),
        "failed_items": restx_fields.List(
            restx_fields.Nested(_batch_delete_error_item)
        ),
    },
)


# ---------------------------------------------------------------------------
# Existing resources (unchanged)
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Batch resources
# ---------------------------------------------------------------------------
@api.route("/batch")
class WidgetBatchResource(Resource):
    """Batch operations for Widgets"""

    @api.expect(_widget_batch_create_request)
    @api.doc(
        responses={
            200: ("All items processed", _widget_batch_create_response),
            207: ("Partial failures", _widget_batch_create_response),
        }
    )
    def post(self):
        """Batch create multiple Widgets.

        Accepts a JSON body with an ``items`` array. Each item is validated
        individually: valid items are created, invalid items are reported in
        ``failed_items`` with their original index.
        """
        body = request.get_json(silent=True) or {}
        items = body.get("items", [])

        if not isinstance(items, list):
            return {"error": "'items' must be a list"}, 400

        successful, failed = WidgetService.create_many(items)

        result = {
            "total": len(items),
            "succeeded": len(successful),
            "failed": len(failed),
            "successful_items": [
                {
                    "widgetId": w.widget_id,
                    "name": w.name,
                    "purpose": w.purpose,
                }
                for w in successful
            ],
            "failed_items": failed,
        }
        status_code = 200 if not failed else 207
        return result, status_code

    @api.expect(_widget_batch_delete_request)
    @api.doc(
        responses={
            200: ("All items processed", _widget_batch_delete_response),
            207: ("Partial failures", _widget_batch_delete_response),
        }
    )
    def delete(self):
        """Batch delete multiple Widgets by ID.

        Accepts a JSON body with an ``ids`` array. IDs that do not exist are
        reported in ``failed_items``; existing IDs are deleted.
        """
        body = request.get_json(silent=True) or {}
        ids = body.get("ids", [])

        if not isinstance(ids, list):
            return {"error": "'ids' must be a list"}, 400

        successful, failed = WidgetService.delete_many(ids)

        result = {
            "total": len(ids),
            "succeeded": len(successful),
            "failed": len(failed),
            "successful_ids": successful,
            "failed_items": failed,
        }
        status_code = 200 if not failed else 207
        return result, status_code
