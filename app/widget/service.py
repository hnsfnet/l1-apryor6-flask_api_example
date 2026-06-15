from app import db
from typing import List
from app.shared.errors import NotFoundError, validate_nonempty, validate_required
from .model import Widget
from .interface import WidgetInterface


class WidgetService:
    @staticmethod
    def get_all() -> List[Widget]:
        return Widget.query.all()

    @staticmethod
    def get_by_id(widget_id: int) -> Widget:
        widget = Widget.query.get(widget_id)
        if widget is None:
            raise NotFoundError("Widget", widget_id)
        return widget

    @staticmethod
    def update(widget: Widget, Widget_change_updates: WidgetInterface) -> Widget:
        validate_nonempty(Widget_change_updates, ("name", "purpose"))
        widget.update(Widget_change_updates)
        db.session.commit()
        return widget

    @staticmethod
    def delete_by_id(widget_id: int) -> int:
        widget = Widget.query.filter(Widget.widget_id == widget_id).first()
        if not widget:
            raise NotFoundError("Widget", widget_id)
        db.session.delete(widget)
        db.session.commit()
        return widget_id

    @staticmethod
    def create(new_attrs: WidgetInterface) -> Widget:
        validate_required(new_attrs, ("name", "purpose"))
        new_widget = Widget(name=new_attrs["name"], purpose=new_attrs["purpose"])

        db.session.add(new_widget)
        db.session.commit()

        return new_widget
