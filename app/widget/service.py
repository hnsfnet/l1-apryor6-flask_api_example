from app import db
from typing import Any, Dict, List, Sequence
from app.shared.bulk import BulkService
from .model import Widget
from .interface import WidgetInterface

WIDGET_FIELDS = ("name", "purpose")


class WidgetService:
    @staticmethod
    def get_all() -> List[Widget]:
        return Widget.query.all()

    @staticmethod
    def get_by_id(widget_id: int) -> Widget:
        return Widget.query.get(widget_id)

    @staticmethod
    def update(widget: Widget, Widget_change_updates: WidgetInterface) -> Widget:
        widget.update(Widget_change_updates)
        db.session.commit()
        return widget

    @staticmethod
    def delete_by_id(widget_id: int) -> List[int]:
        widget = Widget.query.filter(Widget.widget_id == widget_id).first()
        if not widget:
            return []
        db.session.delete(widget)
        db.session.commit()
        return [widget_id]

    @staticmethod
    def create(new_attrs: WidgetInterface) -> Widget:
        new_widget = Widget(name=new_attrs["name"], purpose=new_attrs["purpose"])

        db.session.add(new_widget)
        db.session.commit()

        return new_widget

    @staticmethod
    def create_bulk(items: Sequence[WidgetInterface]) -> Dict[str, Any]:
        """Create many Widgets, reporting per-item success/failure."""
        return BulkService.bulk_create(Widget, items, WIDGET_FIELDS)

    @staticmethod
    def delete_bulk(widget_ids: Sequence[int]) -> Dict[str, Any]:
        """Delete many Widgets by id, reporting which ids were not found."""
        return BulkService.bulk_delete(Widget, Widget.widget_id, widget_ids)
