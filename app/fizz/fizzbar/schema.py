from marshmallow import fields, Schema

from app.shared.query.service import pagination_schema


class FizzbarSchema(Schema):
    """Fizzbar schema"""

    fizzbarId = fields.Number(attribute="fizzbar_id")
    name = fields.String(attribute="name")
    purpose = fields.String(attribute="purpose")


FizzbarPaginationSchema = pagination_schema(FizzbarSchema)
