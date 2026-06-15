from flask_sqlalchemy import SQLAlchemy
from typing import List
from app.test.fixtures import app, db  # noqa
from .model import Widget
from .service import WidgetService  # noqa
from .interface import WidgetInterface


def test_get_all(db: SQLAlchemy):  # noqa
    yin: Widget = Widget(widget_id=1, name="Yin", purpose="thing 1")
    yang: Widget = Widget(widget_id=2, name="Yang", purpose="thing 2")
    db.session.add(yin)
    db.session.add(yang)
    db.session.commit()

    results = WidgetService.get_all()

    assert results["total"] == 2
    assert yin in results["items"] and yang in results["items"]
    assert results["page"] == 1
    assert results["pages"] == 1


def test_get_all_with_pagination(db: SQLAlchemy):  # noqa
    for i in range(1, 11):
        db.session.add(Widget(widget_id=i, name=f"Widget {i}", purpose=f"Purpose {i}"))
    db.session.commit()

    results = WidgetService.get_all({"page": 1, "per_page": 3})

    assert results["total"] == 10
    assert len(results["items"]) == 3
    assert results["page"] == 1
    assert results["pages"] == 4


def test_get_all_with_search(db: SQLAlchemy):  # noqa
    db.session.add(Widget(widget_id=1, name="Alpha Widget", purpose="Testing"))
    db.session.add(Widget(widget_id=2, name="Beta Widget", purpose="Production"))
    db.session.commit()

    results = WidgetService.get_all({"search": "Alpha"})

    assert results["total"] == 1
    assert results["items"][0].name == "Alpha Widget"


def test_get_all_with_sorting(db: SQLAlchemy):  # noqa
    db.session.add(Widget(widget_id=1, name="Charlie", purpose="p"))
    db.session.add(Widget(widget_id=2, name="Alpha", purpose="p"))
    db.session.add(Widget(widget_id=3, name="Bravo", purpose="p"))
    db.session.commit()

    results = WidgetService.get_all({"sort_by": "name", "sort_order": "asc"})

    names = [item.name for item in results["items"]]
    assert names == ["Alpha", "Bravo", "Charlie"]


def test_get_all_empty(db: SQLAlchemy):  # noqa
    results = WidgetService.get_all()
    assert results["total"] == 0
    assert results["items"] == []
    assert results["pages"] == 0


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
