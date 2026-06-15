from flask import jsonify, request
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource
from flask.wrappers import Response
from typing import List

from .schema import FizzbarSchema
from .service import FizzbarService
from .model import Fizzbar
from .interface import FizzbarInterface

api = Namespace("Fizzbar", description="A modular namespace within fizz")  # noqa


@api.route("/")
class FizzbarResource(Resource):
    """Fizzbars"""

    @responds(schema=FizzbarSchema, many=True)
    def get(self) -> List[Fizzbar]:
        """Get all Fizzbars"""

        return FizzbarService.get_all()

    @accepts(schema=FizzbarSchema, api=api)
    @responds(schema=FizzbarSchema)
    @api.response(400, "Request body failed validation")
    def post(self) -> Fizzbar:
        """Create a Single Fizzbar"""

        return FizzbarService.create(request.parsed_obj)


@api.route("/<int:fizzbarId>")
@api.param("fizzbarId", "Fizzbar database ID")
class FizzbarIdResource(Resource):
    @responds(schema=FizzbarSchema)
    @api.response(404, "Fizzbar not found")
    def get(self, fizzbarId: int) -> Fizzbar:
        """Get Single Fizzbar"""

        return FizzbarService.get_by_id(fizzbarId)

    @api.response(200, "Fizzbar deleted")
    @api.response(404, "Fizzbar not found")
    def delete(self, fizzbarId: int) -> Response:
        """Delete Single Fizzbar"""

        id = FizzbarService.delete_by_id(fizzbarId)
        return jsonify(dict(status="Success", id=id))

    @accepts(schema=FizzbarSchema, api=api)
    @responds(schema=FizzbarSchema)
    @api.response(400, "Request body failed validation")
    @api.response(404, "Fizzbar not found")
    def put(self, fizzbarId: int) -> Fizzbar:
        """Update Single Fizzbar"""

        changes: FizzbarInterface = request.parsed_obj
        fizzbar = FizzbarService.get_by_id(fizzbarId)
        return FizzbarService.update(fizzbar, changes)
