from flask import request, jsonify
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource
from flask.wrappers import Response
from typing import Dict, Any

from .schema import FizzbazSchema
from .service import FizzbazService
from .model import Fizzbaz
from .interface import FizzbazInterface
from app.shared.query.service import QueryService

api = Namespace("Fizzbaz", description="A modular namespace within fizz")  # noqa

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
class FizzbazResource(Resource):
    """Fizzbaz"""

    @api.expect(list_parser)
    @api.doc(
        description="Get paginated list of Fizzbaz with optional search and sorting",
        responses={
            200: "Success",
        },
    )
    def get(self) -> Dict[str, Any]:
        """Get all Fizzbaz (paginated)"""
        query_params = QueryService.parse_query_params(request.args)
        result = FizzbazService.get_all(query_params)
        return jsonify(
            {
                "items": FizzbazSchema(many=True).dump(result["items"]),
                "total": result["total"],
                "page": result["page"],
                "per_page": result["per_page"],
                "pages": result["pages"],
            }
        )

    @accepts(schema=FizzbazSchema, api=api)
    @responds(schema=FizzbazSchema)
    def post(self) -> Fizzbaz:
        """Create a Single Fizzbaz"""

        return FizzbazService.create(request.parsed_obj)


@api.route("/<int:fizzbazId>")
@api.param("fizzbazId", "Fizzbaz database ID")
class FizzbazIdResource(Resource):
    @responds(schema=FizzbazSchema)
    def get(self, fizzbazId: int) -> Fizzbaz:
        """Get Single Fizzbaz"""

        return FizzbazService.get_by_id(fizzbazId)

    def delete(self, fizzbazId: int) -> Response:
        """Delete Single Fizzbaz"""

        id = FizzbazService.delete_by_id(fizzbazId)
        return jsonify(dict(status="Success", id=id))

    @accepts(schema=FizzbazSchema, api=api)
    @responds(schema=FizzbazSchema)
    def put(self, fizzbazId: int) -> Fizzbaz:
        """Update Single Fizzbaz"""

        changes: FizzbazInterface = request.parsed_obj
        Fizzbaz = FizzbazService.get_by_id(fizzbazId)
        return FizzbazService.update(Fizzbaz, changes)
