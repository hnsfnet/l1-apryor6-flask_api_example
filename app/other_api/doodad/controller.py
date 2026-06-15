from flask import request, jsonify
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource, fields as restx_fields
from flask.wrappers import Response
from typing import List

from .schema import DoodadSchema
from .service import DoodadService
from .model import Doodad
from .interface import DoodadInterface

api = Namespace("Doodad", description="A modular namespace within Other API")  # noqa

# ---------------------------------------------------------------------------
# Swagger models for batch operations
# ---------------------------------------------------------------------------
_doodad_create_item = api.model(
    "DoodadCreateItem",
    {
        "name": restx_fields.String(required=True, description="Doodad name"),
        "purpose": restx_fields.String(description="Doodad purpose"),
    },
)

_doodad_batch_create_request = api.model(
    "DoodadBatchCreateRequest",
    {
        "items": restx_fields.List(
            restx_fields.Nested(_doodad_create_item),
            description="List of doodads to create",
        )
    },
)

_doodad_batch_delete_request = api.model(
    "DoodadBatchDeleteRequest",
    {
        "ids": restx_fields.List(
            restx_fields.Integer,
            description="List of doodad IDs to delete",
        )
    },
)

_batch_error_item = api.model(
    "DoodadBatchErrorItem",
    {
        "index": restx_fields.Integer(description="Index in the original request"),
        "error": restx_fields.String(description="Error message"),
    },
)

_doodad_batch_create_response = api.model(
    "DoodadBatchCreateResponse",
    {
        "total": restx_fields.Integer(description="Total items requested"),
        "succeeded": restx_fields.Integer(description="Successfully created count"),
        "failed": restx_fields.Integer(description="Failed count"),
        "successful_items": restx_fields.List(
            restx_fields.Nested(
                api.model(
                    "DoodadSummary",
                    {
                        "doodadId": restx_fields.Integer(attribute="doodad_id"),
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
    "DoodadBatchDeleteErrorItem",
    {
        "id": restx_fields.Integer(description="ID that could not be deleted"),
        "error": restx_fields.String(description="Error message"),
    },
)

_doodad_batch_delete_response = api.model(
    "DoodadBatchDeleteResponse",
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


# ---------------------------------------------------------------------------
# Batch resources
# ---------------------------------------------------------------------------
@api.route("/batch")
class DoodadBatchResource(Resource):
    """Batch operations for Doodads"""

    @api.expect(_doodad_batch_create_request)
    @api.doc(
        responses={
            200: ("All items processed", _doodad_batch_create_response),
            207: ("Partial failures", _doodad_batch_create_response),
        }
    )
    def post(self):
        """Batch create multiple Doodads.

        Accepts a JSON body with an ``items`` array. Each item is validated
        individually: valid items are created, invalid items are reported in
        ``failed_items`` with their original index.
        """
        body = request.get_json(silent=True) or {}
        items = body.get("items", [])

        if not isinstance(items, list):
            return {"error": "'items' must be a list"}, 400

        successful, failed = DoodadService.create_many(items)

        result = {
            "total": len(items),
            "succeeded": len(successful),
            "failed": len(failed),
            "successful_items": [
                {
                    "doodadId": d.doodad_id,
                    "name": d.name,
                    "purpose": d.purpose,
                }
                for d in successful
            ],
            "failed_items": failed,
        }
        status_code = 200 if not failed else 207
        return result, status_code

    @api.expect(_doodad_batch_delete_request)
    @api.doc(
        responses={
            200: ("All items processed", _doodad_batch_delete_response),
            207: ("Partial failures", _doodad_batch_delete_response),
        }
    )
    def delete(self):
        """Batch delete multiple Doodads by ID.

        Accepts a JSON body with an ``ids`` array. IDs that do not exist are
        reported in ``failed_items``; existing IDs are deleted.
        """
        body = request.get_json(silent=True) or {}
        ids = body.get("ids", [])

        if not isinstance(ids, list):
            return {"error": "'ids' must be a list"}, 400

        successful, failed = DoodadService.delete_many(ids)

        result = {
            "total": len(ids),
            "succeeded": len(successful),
            "failed": len(failed),
            "successful_ids": successful,
            "failed_items": failed,
        }
        status_code = 200 if not failed else 207
        return result, status_code
