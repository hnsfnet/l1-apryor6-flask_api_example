from app import db
from typing import List, Tuple, Dict
from .model import Widget
from .interface import WidgetInterface
from app.shared.batch import batch_create, batch_delete


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
    def create_many(items: List[dict]) -> Tuple[List[Widget], List[Dict]]:
        """
        Batch create widgets.

        Args:
            items: List of dicts with 'name' and optional 'purpose'.

        Returns:
            Tuple of (successful_widgets, failed_items).
        """
        return batch_create(Widget, items)

    @staticmethod
    def delete_many(ids: List[int]) -> Tuple[List[int], List[Dict]]:
        """
        Batch delete widgets by ID.

        Args:
            ids: List of widget IDs to delete.

        Returns:
            Tuple of (successful_ids, failed_items).
        """
        return batch_delete(Widget, ids, Widget.widget_id)
