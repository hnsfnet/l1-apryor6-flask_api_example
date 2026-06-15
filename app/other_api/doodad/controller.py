from flask import request
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource, fields as rx_fields
from flask.wrappers import Response
from typing import List

from .schema import DoodadSchema
from .service import DoodadService
from .model import Doodad
from .interface import DoodadInterface

api = Namespace("Doodad", description="A modular namespace within Other API")  # noqa

doodad_item = api.model(
    "DoodadInput",
    {
        "name": rx_fields.String(required=True, description="Doodad name"),
        "purpose": rx_fields.String(required=True, description="Doodad purpose"),
    },
)

doodad_entity = api.model(
    "Doodad",
    {
        "doodadId": rx_fields.Integer(description="Doodad database ID"),
        "name": rx_fields.String(),
        "purpose": rx_fields.String(),
    },
)

doodad_create_failure = api.model(
    "DoodadBulkCreateFailure",
    {
        "index": rx_fields.Integer(description="Position in the submitted list"),
        "item": rx_fields.Raw(description="The submitted payload that was rejected"),
        "error": rx_fields.String(description="Why the item was rejected"),
    },
)

doodad_bulk_create_request = api.model(
    "DoodadBulkCreateRequest",
    {
        "items": rx_fields.List(
            rx_fields.Nested(doodad_item),
            required=True,
            description="Doodads to create",
        )
    },
)

doodad_bulk_create_response = api.model(
    "DoodadBulkCreateResponse",
    {
        "success_count": rx_fields.Integer(description="Number of doodads created"),
        "failure_count": rx_fields.Integer(description="Number of rejected items"),
        "succeeded": rx_fields.List(rx_fields.Nested(doodad_entity)),
        "failed": rx_fields.List(rx_fields.Nested(doodad_create_failure)),
    },
)

doodad_bulk_delete_request = api.model(
    "DoodadBulkDeleteRequest",
    {
        "ids": rx_fields.List(
            rx_fields.Integer,
            required=True,
            description="Doodad IDs to delete",
        )
    },
)

doodad_bulk_delete_response = api.model(
    "DoodadBulkDeleteResponse",
    {
        "success_count": rx_fields.Integer(description="Number of doodads deleted"),
        "failure_count": rx_fields.Integer(description="Number of ids not found"),
        "requested": rx_fields.List(rx_fields.Integer, description="Ids as received"),
        "deleted": rx_fields.List(rx_fields.Integer),
        "not_found": rx_fields.List(rx_fields.Integer),
    },
)


@api.route("/")
class DoodadResource(Resource):
    """Doodads"""

    @responds(schema=DoodadSchema, many=True)
    def get(self) -> List[Doodad]:
        """Get all Doodads"""

        return DoodadService.get_all()

    @accepts(schema=DoodadSchema, api=api)
    @responds(schema=DoodadSchema)
    def post(self) -> Doodad:
        """Create a Single Doodad"""

        return DoodadService.create(request.parsed_obj)


@api.route("/<int:doodadId>")
@api.param("doodadId", "Doodad database ID")
class DoodadIdResource(Resource):
    @responds(schema=DoodadSchema)
    def get(self, doodadId: int) -> Doodad:
        """Get Single Doodad"""

        return DoodadService.get_by_id(doodadId)

    def delete(self, doodadId: int) -> Response:
        """Delete Single Doodad"""
        from flask import jsonify

        print("doodadId = ", doodadId)
        id = DoodadService.delete_by_id(doodadId)
        return jsonify(dict(status="Success", id=id))

    @accepts(schema=DoodadSchema, api=api)
    @responds(schema=DoodadSchema)
    def put(self, doodadId: int) -> Doodad:
        """Update Single Doodad"""

        changes: DoodadInterface = request.parsed_obj
        Doodad = DoodadService.get_by_id(doodadId)
        return DoodadService.update(Doodad, changes)


@api.route("/bulk")
class DoodadBulkResource(Resource):
    """Create or delete many Doodads in a single request"""

    @api.expect(doodad_bulk_create_request)
    @api.marshal_with(doodad_bulk_create_response)
    def post(self):
        """Create a batch of Doodads

        Send ``{"items": [{"name": ..., "purpose": ...}, ...]}``. Valid items
        are created even if others are rejected; the response reports how many
        succeeded, how many failed and exactly which items failed and why.
        """
        payload = request.get_json(silent=True) or {}
        result = DoodadService.create_bulk(payload.get("items", []))
        return {
            "success_count": result["success_count"],
            "failure_count": result["failure_count"],
            "succeeded": DoodadSchema(many=True).dump(result["succeeded"]),
            "failed": result["failed"],
        }

    @api.expect(doodad_bulk_delete_request)
    @api.marshal_with(doodad_bulk_delete_response)
    def delete(self):
        """Delete a batch of Doodads by id

        Send ``{"ids": [1, 2, 3]}``. Ids that do not exist (or were already
        deleted earlier in the same request) are returned under ``not_found``
        instead of failing the whole call.
        """
        payload = request.get_json(silent=True) or {}
        return DoodadService.delete_bulk(payload.get("ids", []))
