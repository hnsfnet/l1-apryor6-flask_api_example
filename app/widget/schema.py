from marshmallow import fields, Schema

from app.shared.query.service import pagination_schema


class WidgetSchema(Schema):
    """Widget schema"""

    widgetId = fields.Number(attribute="widget_id")
    name = fields.String(attribute="name")
    purpose = fields.String(attribute="purpose")


WidgetPaginationSchema = pagination_schema(WidgetSchema)
