from flask import request
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource
from flask.wrappers import Response
from typing import List

from app.shared.errors import NotFoundException, ValidationError, error_response, register_error_models
from .schema import FizzbarSchema
from .service import FizzbarService
from .model import Fizzbar
from .interface import FizzbarInterface

api = Namespace("Fizzbar", description="A modular namespace within fizz")  # noqa
error_model = register_error_models(api)


@api.route("/")
class FizzbarResource(Resource):
    """Fizzbars"""

    @responds(schema=FizzbarSchema, many=True)
    def get(self) -> List[Fizzbar]:
        """Get all Fizzbars"""

        return FizzbarService.get_all()

    @accepts(schema=FizzbarSchema, api=api)
    @responds(schema=FizzbarSchema)
    @api.response(400, "Validation error", error_model)
    def post(self) -> Fizzbar:
        """Create a Single Fizzbar

        Requires ``name`` and ``purpose`` to be non-empty strings.
        """

        _validate_fizzbar_payload(request.parsed_obj)
        return FizzbarService.create(request.parsed_obj)


@api.route("/<int:fizzbarId>")
@api.param("fizzbarId", "Fizzbar database ID")
class FizzbarIdResource(Resource):
    @responds(schema=FizzbarSchema)
    @api.response(404, "Fizzbar not found", error_model)
    def get(self, fizzbarId: int) -> Fizzbar:
        """Get Single Fizzbar"""

        fizzbar = FizzbarService.get_by_id(fizzbarId)
        if not fizzbar:
            raise NotFoundException("Fizzbar", fizzbarId)
        return fizzbar

    @api.response(200, "Success")
    @api.response(404, "Fizzbar not found", error_model)
    def delete(self, fizzbarId: int) -> Response:
        """Delete Single Fizzbar"""
        from flask import jsonify

        fizzbar = FizzbarService.get_by_id(fizzbarId)
        if not fizzbar:
            raise NotFoundException("Fizzbar", fizzbarId)
        FizzbarService.delete_by_id(fizzbarId)
        return jsonify(dict(status="Success", id=[fizzbarId]))

    @accepts(schema=FizzbarSchema, api=api)
    @responds(schema=FizzbarSchema)
    @api.response(400, "Validation error", error_model)
    @api.response(404, "Fizzbar not found", error_model)
    def put(self, fizzbarId: int) -> Fizzbar:
        """Update Single Fizzbar"""

        changes: FizzbarInterface = request.parsed_obj
        fizzbar = FizzbarService.get_by_id(fizzbarId)
        if not fizzbar:
            raise NotFoundException("Fizzbar", fizzbarId)
        return FizzbarService.update(fizzbar, changes)


def _validate_fizzbar_payload(data: dict) -> None:
    """Raise ValidationError if required fields are missing or empty."""
    errors = {}
    for field in ("name", "purpose"):
        value = data.get(field)
        if value is None or (isinstance(value, str) and value.strip() == ""):
            errors[field] = f"Field '{field}' is required and must not be empty."
    if errors:
        raise ValidationError(message="Invalid request body", details=errors)
