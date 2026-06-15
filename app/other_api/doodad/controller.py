from flask import request
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource
from flask.wrappers import Response
from typing import List

from app.shared.errors import NotFoundException, ValidationError, error_response, register_error_models
from .schema import DoodadSchema
from .service import DoodadService
from .model import Doodad
from .interface import DoodadInterface

api = Namespace("Doodad", description="A modular namespace within Other API")  # noqa
error_model = register_error_models(api)


@api.route("/")
class DoodadResource(Resource):
    """Doodads"""

    @responds(schema=DoodadSchema, many=True)
    def get(self) -> List[Doodad]:
        """Get all Doodads"""

        return DoodadService.get_all()

    @accepts(schema=DoodadSchema, api=api)
    @responds(schema=DoodadSchema)
    @api.response(400, "Validation error", error_model)
    def post(self) -> Doodad:
        """Create a Single Doodad

        Requires ``name`` and ``purpose`` to be non-empty strings.
        """

        _validate_doodad_payload(request.parsed_obj)
        return DoodadService.create(request.parsed_obj)


@api.route("/<int:doodadId>")
@api.param("doodadId", "Doodad database ID")
class DoodadIdResource(Resource):
    @responds(schema=DoodadSchema)
    @api.response(404, "Doodad not found", error_model)
    def get(self, doodadId: int) -> Doodad:
        """Get Single Doodad"""

        doodad = DoodadService.get_by_id(doodadId)
        if not doodad:
            raise NotFoundException("Doodad", doodadId)
        return doodad

    @api.response(200, "Success")
    @api.response(404, "Doodad not found", error_model)
    def delete(self, doodadId: int) -> Response:
        """Delete Single Doodad"""
        from flask import jsonify

        doodad = DoodadService.get_by_id(doodadId)
        if not doodad:
            raise NotFoundException("Doodad", doodadId)
        DoodadService.delete_by_id(doodadId)
        return jsonify(dict(status="Success", id=[doodadId]))

    @accepts(schema=DoodadSchema, api=api)
    @responds(schema=DoodadSchema)
    @api.response(400, "Validation error", error_model)
    @api.response(404, "Doodad not found", error_model)
    def put(self, doodadId: int) -> Doodad:
        """Update Single Doodad"""

        changes: DoodadInterface = request.parsed_obj
        doodad = DoodadService.get_by_id(doodadId)
        if not doodad:
            raise NotFoundException("Doodad", doodadId)
        return DoodadService.update(doodad, changes)


def _validate_doodad_payload(data: dict) -> None:
    """Raise ValidationError if required fields are missing or empty."""
    errors = {}
    for field in ("name", "purpose"):
        value = data.get(field)
        if value is None or (isinstance(value, str) and value.strip() == ""):
            errors[field] = f"Field '{field}' is required and must not be empty."
    if errors:
        raise ValidationError(message="Invalid request body", details=errors)
