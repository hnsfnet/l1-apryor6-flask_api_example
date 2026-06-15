from flask import request
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource
from flask.wrappers import Response
from typing import List

from app.shared.errors import NotFoundException, ValidationError, error_response, register_error_models
from .schema import WhatsitSchema
from .service import WhatsitService
from .model import Whatsit
from .interface import WhatsitInterface

api = Namespace('Whatsit', description='A modular namespace within Other API')  # noqa
error_model = register_error_models(api)


@api.route('/')
class WhatsitResource(Resource):
    '''Whatsits'''

    @responds(schema=WhatsitSchema, many=True)
    def get(self) -> List[Whatsit]:
        '''Get all Whatsits'''

        return WhatsitService.get_all()

    @accepts(schema=WhatsitSchema, api=api)
    @responds(schema=WhatsitSchema)
    @api.response(400, "Validation error", error_model)
    def post(self) -> Whatsit:
        '''Create a Single Whatsit

        Requires ``name`` and ``purpose`` to be non-empty strings.
        '''

        _validate_whatsit_payload(request.parsed_obj)
        return WhatsitService.create(request.parsed_obj)


@api.route('/<int:whatsitId>')
@api.param('whatsitId', 'Whatsit database ID')
class WhatsitIdResource(Resource):
    @responds(schema=WhatsitSchema)
    @api.response(404, "Whatsit not found", error_model)
    def get(self, whatsitId: int) -> Whatsit:
        '''Get Single Whatsit'''

        whatsit = WhatsitService.get_by_id(whatsitId)
        if not whatsit:
            raise NotFoundException("Whatsit", whatsitId)
        return whatsit

    @api.response(200, "Success")
    @api.response(404, "Whatsit not found", error_model)
    def delete(self, whatsitId: int) -> Response:
        '''Delete Single Whatsit'''
        from flask import jsonify

        whatsit = WhatsitService.get_by_id(whatsitId)
        if not whatsit:
            raise NotFoundException("Whatsit", whatsitId)
        WhatsitService.delete_by_id(whatsitId)
        return jsonify(dict(status='Success', id=[whatsitId]))

    @accepts(schema=WhatsitSchema, api=api)
    @responds(schema=WhatsitSchema)
    @api.response(400, "Validation error", error_model)
    @api.response(404, "Whatsit not found", error_model)
    def put(self, whatsitId: int) -> Whatsit:
        '''Update Single Whatsit'''

        changes: WhatsitInterface = request.parsed_obj
        whatsit = WhatsitService.get_by_id(whatsitId)
        if not whatsit:
            raise NotFoundException("Whatsit", whatsitId)
        return WhatsitService.update(whatsit, changes)


def _validate_whatsit_payload(data: dict) -> None:
    """Raise ValidationError if required fields are missing or empty."""
    errors = {}
    for field in ("name", "purpose"):
        value = data.get(field)
        if value is None or (isinstance(value, str) and value.strip() == ""):
            errors[field] = f"Field '{field}' is required and must not be empty."
    if errors:
        raise ValidationError(message="Invalid request body", details=errors)
