from marshmallow import fields, Schema

from app.shared.query.service import pagination_schema


class FizzbazSchema(Schema):
    """Fizzbaz schema"""

    fizzbazId = fields.Number(attribute="fizzbaz_id")
    name = fields.String(attribute="name")
    purpose = fields.String(attribute="purpose")


FizzbazPaginationSchema = pagination_schema(FizzbazSchema)
