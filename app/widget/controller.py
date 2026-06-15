from flask import request, jsonify
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource
from flask.wrappers import Response
from typing import Dict, Any

from .schema import WidgetSchema
from .service import WidgetService
from .model import Widget
from .interface import WidgetInterface
from app.shared.query.service import QueryService

api = Namespace("Widget", description="Single namespace, single entity")  # noqa

# Swagger query parser for list endpoints
list_parser = api.parser()
list_parser.add_argument(
    "page", type=int, default=1, location="args", help="Page number (1-based)"
)
list_parser.add_argument(
    "per_page",
    type=int,
    default=20,
    location="args",
    help="Number of items per page (max 100)",
)
list_parser.add_argument(
    "search",
    type=str,
    required=False,
    location="args",
    help="Search term for fuzzy matching on name and purpose",
)
list_parser.add_argument(
    "sort_by",
    type=str,
    default="id",
    choices=["id", "name"],
    location="args",
    help="Field to sort by",
)
list_parser.add_argument(
    "sort_order",
    type=str,
    default="asc",
    choices=["asc", "desc"],
    location="args",
    help="Sort direction",
)


@api.route("/")
class WidgetResource(Resource):
    """Widgets"""

    @api.expect(list_parser)
    @api.doc(
        description="Get paginated list of Widgets with optional search and sorting",
        responses={
            200: "Success",
        },
    )
    def get(self) -> Dict[str, Any]:
        """Get all Widgets (paginated)"""
        query_params = QueryService.parse_query_params(request.args)
        result = WidgetService.get_all(query_params)
        return jsonify(
            {
                "items": WidgetSchema(many=True).dump(result["items"]),
                "total": result["total"],
                "page": result["page"],
                "per_page": result["per_page"],
                "pages": result["pages"],
            }
        )

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

        id = WidgetService.delete_by_id(widgetId)
        return jsonify(dict(status="Success", id=id))

    @accepts(schema=WidgetSchema, api=api)
    @responds(schema=WidgetSchema)
    def put(self, widgetId: int) -> Widget:
        """Update Single Widget"""

        changes: WidgetInterface = request.parsed_obj
        Widget = WidgetService.get_by_id(widgetId)
        return WidgetService.update(Widget, changes)
