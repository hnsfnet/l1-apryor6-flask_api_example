from flask_sqlalchemy import SQLAlchemy
from typing import List
import pytest
from app.test.fixtures import app, db  # noqa
from app.shared.errors import NotFoundError, ValidationError
from .model import Widget
from .service import WidgetService  # noqa
from .interface import WidgetInterface


def test_get_all(db: SQLAlchemy):  # noqa
    yin: Widget = Widget(widget_id=1, name="Yin", purpose="thing 1")
    yang: Widget = Widget(widget_id=2, name="Yang", purpose="thing 2")
    db.session.add(yin)
    db.session.add(yang)
    db.session.commit()

    results: List[Widget] = WidgetService.get_all()

    assert len(results) == 2
    assert yin in results and yang in results


def test_update(db: SQLAlchemy):  # noqa
    yin: Widget = Widget(widget_id=1, name="Yin", purpose="thing 1")

    db.session.add(yin)
    db.session.commit()
    updates: WidgetInterface = dict(name="New Widget name")

    WidgetService.update(yin, updates)

    result: Widget = Widget.query.get(yin.widget_id)
    assert result.name == "New Widget name"


def test_delete_by_id(db: SQLAlchemy):  # noqa
    yin: Widget = Widget(widget_id=1, name="Yin", purpose="thing 1")
    yang: Widget = Widget(widget_id=2, name="Yang", purpose="thing 2")
    db.session.add(yin)
    db.session.add(yang)
    db.session.commit()

    WidgetService.delete_by_id(1)
    db.session.commit()

    results: List[Widget] = Widget.query.all()

    assert len(results) == 1
    assert yin not in results and yang in results


def test_create(db: SQLAlchemy):  # noqa

    yin: WidgetInterface = dict(name="Fancy new widget", purpose="Fancy new purpose")
    WidgetService.create(yin)
    results: List[Widget] = Widget.query.all()

    assert len(results) == 1

    for k in yin.keys():
        assert getattr(results[0], k) == yin[k]


def test_get_by_id_not_found(db: SQLAlchemy):  # noqa
    with pytest.raises(NotFoundError):
        WidgetService.get_by_id(999)


def test_delete_by_id_not_found(db: SQLAlchemy):  # noqa
    with pytest.raises(NotFoundError):
        WidgetService.delete_by_id(999)


def test_create_missing_fields_rejected(db: SQLAlchemy):  # noqa
    with pytest.raises(ValidationError):
        WidgetService.create(dict(name="only a name"))
    assert Widget.query.all() == []


def test_update_empty_field_rejected(db: SQLAlchemy):  # noqa
    widget: Widget = Widget(widget_id=1, name="Original", purpose="Original")
    db.session.add(widget)
    db.session.commit()
    with pytest.raises(ValidationError):
        WidgetService.update(widget, dict(name=""))
