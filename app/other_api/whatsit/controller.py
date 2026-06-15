from flask import jsonify, request
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource
from flask.wrappers import Response
from typing import List

from .schema import WhatsitSchema
from .service import WhatsitService
from .model import Whatsit
from .interface import WhatsitInterface

api = Namespace('Whatsit', description='A modular namespace within Other API')  # noqa


@api.route('/')
class WhatsitResource(Resource):
    '''Whatsits'''

    @responds(schema=WhatsitSchema, many=True)
    def get(self) -> List[Whatsit]:
        '''Get all Whatsits'''

        return WhatsitService.get_all()

    @accepts(schema=WhatsitSchema, api=api)
    @responds(schema=WhatsitSchema)
    @api.response(400, 'Request body failed validation')
    def post(self) -> Whatsit:
        '''Create a Single Whatsit'''

        return WhatsitService.create(request.parsed_obj)


@api.route('/<int:whatsitId>')
@api.param('whatsitId', 'Whatsit database ID')
class WhatsitIdResource(Resource):
    @responds(schema=WhatsitSchema)
    @api.response(404, 'Whatsit not found')
    def get(self, whatsitId: int) -> Whatsit:
        '''Get Single Whatsit'''

        return WhatsitService.get_by_id(whatsitId)

    @api.response(200, 'Whatsit deleted')
    @api.response(404, 'Whatsit not found')
    def delete(self, whatsitId: int) -> Response:
        '''Delete Single Whatsit'''

        id = WhatsitService.delete_by_id(whatsitId)
        return jsonify(dict(status='Success', id=id))

    @accepts(schema=WhatsitSchema, api=api)
    @responds(schema=WhatsitSchema)
    @api.response(400, 'Request body failed validation')
    @api.response(404, 'Whatsit not found')
    def put(self, whatsitId: int) -> Whatsit:
        '''Update Single Whatsit'''

        changes: WhatsitInterface = request.parsed_obj
        whatsit = WhatsitService.get_by_id(whatsitId)
        return WhatsitService.update(whatsit, changes)
