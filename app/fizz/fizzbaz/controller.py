from flask import request
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource
from flask.wrappers import Response
from typing import List

from app.shared.errors import NotFoundException, ValidationError, error_response, register_error_models
from .schema import FizzbazSchema
from .service import FizzbazService
from .model import Fizzbaz
from .interface import FizzbazInterface

api = Namespace("Fizzbaz", description="A modular namespace within fizz")  # noqa
error_model = register_error_models(api)


@api.route("/")
class FizzbazResource(Resource):
    """Fizzbaz"""

    @responds(schema=FizzbazSchema, many=True)
    def get(self) -> List[Fizzbaz]:
        """Get all Fizzbaz"""

        return FizzbazService.get_all()

    @accepts(schema=FizzbazSchema, api=api)
    @responds(schema=FizzbazSchema)
    @api.response(400, "Validation error", error_model)
    def post(self) -> Fizzbaz:
        """Create a Single Fizzbaz

        Requires ``name`` and ``purpose`` to be non-empty strings.
        """

        _validate_fizzbaz_payload(request.parsed_obj)
        return FizzbazService.create(request.parsed_obj)


@api.route("/<int:fizzbazId>")
@api.param("fizzbazId", "Fizzbaz database ID")
class FizzbazIdResource(Resource):
    @responds(schema=FizzbazSchema)
    @api.response(404, "Fizzbaz not found", error_model)
    def get(self, fizzbazId: int) -> Fizzbaz:
        """Get Single Fizzbaz"""

        fizzbaz = FizzbazService.get_by_id(fizzbazId)
        if not fizzbaz:
            raise NotFoundException("Fizzbaz", fizzbazId)
        return fizzbaz

    @api.response(200, "Success")
    @api.response(404, "Fizzbaz not found", error_model)
    def delete(self, fizzbazId: int) -> Response:
        """Delete Single Fizzbaz"""
        from flask import jsonify

        fizzbaz = FizzbazService.get_by_id(fizzbazId)
        if not fizzbaz:
            raise NotFoundException("Fizzbaz", fizzbazId)
        FizzbazService.delete_by_id(fizzbazId)
        return jsonify(dict(status="Success", id=[fizzbazId]))

    @accepts(schema=FizzbazSchema, api=api)
    @responds(schema=FizzbazSchema)
    @api.response(400, "Validation error", error_model)
    @api.response(404, "Fizzbaz not found", error_model)
    def put(self, fizzbazId: int) -> Fizzbaz:
        """Update Single Fizzbaz"""

        changes: FizzbazInterface = request.parsed_obj
        fizzbaz = FizzbazService.get_by_id(fizzbazId)
        if not fizzbaz:
            raise NotFoundException("Fizzbaz", fizzbazId)
        return FizzbazService.update(fizzbaz, changes)


def _validate_fizzbaz_payload(data: dict) -> None:
    """Raise ValidationError if required fields are missing or empty."""
    errors = {}
    for field in ("name", "purpose"):
        value = data.get(field)
        if value is None or (isinstance(value, str) and value.strip() == ""):
            errors[field] = f"Field '{field}' is required and must not be empty."
    if errors:
        raise ValidationError(message="Invalid request body", details=errors)
