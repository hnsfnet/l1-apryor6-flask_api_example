from flask import request, jsonify
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource
from flask.wrappers import Response
from typing import Dict, Any

from .schema import FizzbarSchema
from .service import FizzbarService
from .model import Fizzbar
from .interface import FizzbarInterface
from app.shared.query.service import QueryService

api = Namespace("Fizzbar", description="A modular namespace within fizz")  # noqa

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
class FizzbarResource(Resource):
    """Fizzbars"""

    @api.expect(list_parser)
    @api.doc(
        description="Get paginated list of Fizzbars with optional search and sorting",
        responses={
            200: "Success",
        },
    )
    def get(self) -> Dict[str, Any]:
        """Get all Fizzbars (paginated)"""
        query_params = QueryService.parse_query_params(request.args)
        result = FizzbarService.get_all(query_params)
        return jsonify(
            {
                "items": FizzbarSchema(many=True).dump(result["items"]),
                "total": result["total"],
                "page": result["page"],
                "per_page": result["per_page"],
                "pages": result["pages"],
            }
        )

    @accepts(schema=FizzbarSchema, api=api)
    @responds(schema=FizzbarSchema)
    def post(self) -> Fizzbar:
        """Create a Single Fizzbar"""

        return FizzbarService.create(request.parsed_obj)


@api.route("/<int:fizzbarId>")
@api.param("fizzbarId", "Fizzbar database ID")
class FizzbarIdResource(Resource):
    @responds(schema=FizzbarSchema)
    def get(self, fizzbarId: int) -> Fizzbar:
        """Get Single Fizzbar"""

        return FizzbarService.get_by_id(fizzbarId)

    def delete(self, fizzbarId: int) -> Response:
        """Delete Single Fizzbar"""

        print("fizzbarId = ", fizzbarId)
        id = FizzbarService.delete_by_id(fizzbarId)
        return jsonify(dict(status="Success", id=id))

    @accepts(schema=FizzbarSchema, api=api)
    @responds(schema=FizzbarSchema)
    def put(self, fizzbarId: int) -> Fizzbar:
        """Update Single Fizzbar"""

        changes: FizzbarInterface = request.parsed_obj
        Fizzbar = FizzbarService.get_by_id(fizzbarId)
        return FizzbarService.update(Fizzbar, changes)
