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


# ---------------------------------------------------------------------------
# Batch create tests
# ---------------------------------------------------------------------------
def test_create_many_all_valid(db: SQLAlchemy):  # noqa
    items = [
        {"name": "Widget A", "purpose": "Purpose A"},
        {"name": "Widget B", "purpose": "Purpose B"},
        {"name": "Widget C", "purpose": "Purpose C"},
    ]
    successful, failed = WidgetService.create_many(items)

    assert len(successful) == 3
    assert len(failed) == 0
    assert all(isinstance(w, Widget) for w in successful)

    results = Widget.query.all()
    assert len(results) == 3


def test_create_many_partial_failure(db: SQLAlchemy):  # noqa
    items = [
        {"name": "Valid Widget", "purpose": "OK"},
        {"purpose": "Missing name"},  # invalid: no name
        {"name": "Another Valid", "purpose": "OK"},
    ]
    successful, failed = WidgetService.create_many(items)

    assert len(successful) == 2
    assert len(failed) == 1
    assert failed[0]["index"] == 1
    assert "name" in failed[0]["error"].lower()

    results = Widget.query.all()
    assert len(results) == 2


def test_create_many_all_invalid(db: SQLAlchemy):  # noqa
    items = [
        {"purpose": "No name 1"},
        {"purpose": "No name 2"},
    ]
    successful, failed = WidgetService.create_many(items)

    assert len(successful) == 0
    assert len(failed) == 2

    results = Widget.query.all()
    assert len(results) == 0


def test_create_many_empty_list(db: SQLAlchemy):  # noqa
    successful, failed = WidgetService.create_many([])

    assert len(successful) == 0
    assert len(failed) == 0

    results = Widget.query.all()
    assert len(results) == 0


def test_create_many_non_dict_items(db: SQLAlchemy):  # noqa
    items = ["not a dict", 42, {"name": "Valid"}]
    successful, failed = WidgetService.create_many(items)

    assert len(successful) == 1
    assert len(failed) == 2
    assert failed[0]["index"] == 0
    assert failed[1]["index"] == 1


def test_create_many_empty_name(db: SQLAlchemy):  # noqa
    items = [
        {"name": "", "purpose": "Empty name"},
        {"name": "   ", "purpose": "Whitespace name"},
        {"name": "Valid", "purpose": "OK"},
    ]
    successful, failed = WidgetService.create_many(items)

    assert len(successful) == 1
    assert len(failed) == 2


# ---------------------------------------------------------------------------
# Batch delete tests
# ---------------------------------------------------------------------------
def test_delete_many_all_exist(db: SQLAlchemy):  # noqa
    w1 = Widget(widget_id=1, name="W1", purpose="P1")
    w2 = Widget(widget_id=2, name="W2", purpose="P2")
    w3 = Widget(widget_id=3, name="W3", purpose="P3")
    db.session.add_all([w1, w2, w3])
    db.session.commit()

    successful, failed = WidgetService.delete_many([1, 2, 3])

    assert successful == [1, 2, 3]
    assert len(failed) == 0
    assert len(Widget.query.all()) == 0


def test_delete_many_partial_not_found(db: SQLAlchemy):  # noqa
    w1 = Widget(widget_id=1, name="W1", purpose="P1")
    w2 = Widget(widget_id=2, name="W2", purpose="P2")
    db.session.add_all([w1, w2])
    db.session.commit()

    successful, failed = WidgetService.delete_many([1, 99, 2, 88])

    assert set(successful) == {1, 2}
    assert len(failed) == 2
    failed_ids = {f["id"] for f in failed}
    assert failed_ids == {99, 88}
    assert len(Widget.query.all()) == 0


def test_delete_many_none_exist(db: SQLAlchemy):  # noqa
    successful, failed = WidgetService.delete_many([100, 200, 300])

    assert len(successful) == 0
    assert len(failed) == 3


def test_delete_many_empty_list(db: SQLAlchemy):  # noqa
    successful, failed = WidgetService.delete_many([])

    assert len(successful) == 0
    assert len(failed) == 0


def test_delete_many_duplicate_ids(db: SQLAlchemy):  # noqa
    w1 = Widget(widget_id=1, name="W1", purpose="P1")
    db.session.add(w1)
    db.session.commit()

    successful, failed = WidgetService.delete_many([1, 1, 1])

    # First occurrence succeeds, subsequent ones should fail (already deleted)
    assert len(successful) == 1
    assert successful[0] == 1
    assert len(failed) == 2
    assert all(f["id"] == 1 for f in failed)
    assert len(Widget.query.all()) == 0
