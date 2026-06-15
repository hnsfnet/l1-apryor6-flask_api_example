from flask_sqlalchemy import SQLAlchemy
from typing import List

from app.test.fixtures import app, db  # noqa
from app.widget.model import Widget
from app.shared.bulk import BulkService

FIELDS = ("name", "purpose")


def test_bulk_create_all_success(db: SQLAlchemy):  # noqa
    items = [
        dict(name="One", purpose="p1"),
        dict(name="Two", purpose="p2"),
    ]

    result = BulkService.bulk_create(Widget, items, FIELDS)

    assert result["success_count"] == 2
    assert result["failure_count"] == 0
    assert result["failed"] == []
    assert len(result["succeeded"]) == 2
    assert len(Widget.query.all()) == 2


def test_bulk_create_partial_failure_persists_valid_rows(db: SQLAlchemy):  # noqa
    items = [
        dict(name="Good", purpose="p1"),
        dict(name="Missing purpose"),
        "not even an object",
    ]

    result = BulkService.bulk_create(Widget, items, FIELDS)

    assert result["success_count"] == 1
    assert result["failure_count"] == 2

    # The valid row is written even though others were rejected.
    rows: List[Widget] = Widget.query.all()
    assert len(rows) == 1
    assert rows[0].name == "Good"

    # Failures carry the original index, payload and a reason.
    by_index = {f["index"]: f for f in result["failed"]}
    assert "purpose" in by_index[1]["error"]
    assert by_index[1]["item"] == dict(name="Missing purpose")
    assert "object" in by_index[2]["error"]


def test_bulk_create_db_error_rolls_back_only_failing_row(db: SQLAlchemy):  # noqa
    # The test above covers items rejected by validation *before* they reach
    # the database. This covers the other partial-failure path: an item that
    # passes validation but raises at the database layer (here, a value the
    # column cannot bind). Its savepoint must roll back on its own without
    # discarding the valid rows created before and after it.
    items = [
        dict(name="Good A", purpose="p"),
        dict(name={"bad": "bind"}, purpose="p"),  # passes None-check, fails at bind
        dict(name="Good B", purpose="p"),
    ]

    result = BulkService.bulk_create(Widget, items, FIELDS)

    assert result["success_count"] == 2
    assert result["failure_count"] == 1

    # Only the offending row is reported, keeping its original index and payload.
    assert [f["index"] for f in result["failed"]] == [1]
    assert result["failed"][0]["item"] == dict(name={"bad": "bind"}, purpose="p")
    assert result["failed"][0]["error"]  # a non-empty database error message

    # The rows on either side of the failure are still persisted.
    rows: List[Widget] = Widget.query.all()
    assert {r.name for r in rows} == {"Good A", "Good B"}


def test_bulk_create_empty_list_is_a_noop(db: SQLAlchemy):  # noqa
    result = BulkService.bulk_create(Widget, [], FIELDS)

    assert result["success_count"] == 0
    assert result["failure_count"] == 0
    assert result["succeeded"] == []
    assert result["failed"] == []
    assert Widget.query.all() == []


def _seed(db, *ids):
    for i in ids:
        db.session.add(Widget(widget_id=i, name=f"w{i}", purpose="p"))
    db.session.commit()


def test_bulk_delete_success(db: SQLAlchemy):  # noqa
    _seed(db, 1, 2)

    result = BulkService.bulk_delete(Widget, Widget.widget_id, [1, 2])

    assert result["deleted"] == [1, 2]
    assert result["not_found"] == []
    assert result["success_count"] == 2
    assert result["failure_count"] == 0
    assert Widget.query.all() == []


def test_bulk_delete_missing_ids_reported_not_raised(db: SQLAlchemy):  # noqa
    _seed(db, 1)

    result = BulkService.bulk_delete(Widget, Widget.widget_id, [1, 99])

    assert result["deleted"] == [1]
    assert result["not_found"] == [99]
    assert result["success_count"] == 1
    assert result["failure_count"] == 1


def test_bulk_delete_duplicate_ids(db: SQLAlchemy):  # noqa
    _seed(db, 1, 2)

    result = BulkService.bulk_delete(Widget, Widget.widget_id, [1, 1, 2])

    # First occurrence deletes; the duplicate then finds nothing.
    assert result["requested"] == [1, 1, 2]
    assert result["deleted"] == [1, 2]
    assert result["not_found"] == [1]
    assert result["success_count"] == 2
    assert result["failure_count"] == 1
    assert Widget.query.all() == []


def test_bulk_delete_empty_list_is_a_noop(db: SQLAlchemy):  # noqa
    _seed(db, 1)

    result = BulkService.bulk_delete(Widget, Widget.widget_id, [])

    assert result["deleted"] == []
    assert result["not_found"] == []
    assert result["success_count"] == 0
    assert result["failure_count"] == 0
    assert len(Widget.query.all()) == 1
