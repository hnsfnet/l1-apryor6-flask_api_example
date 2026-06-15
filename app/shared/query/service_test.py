import pytest
from app.test.fixtures import app, client, db  # noqa
from app.shared.query.service import QueryService


def test_get_count_empty(db):  # noqa
    from app.widget.model import Widget
    assert QueryService.get_count(Widget) == 0


def test_get_count_with_data(db):  # noqa
    from app.widget.model import Widget
    db.session.bulk_insert_mappings(
        Widget, [{"name": "W1", "purpose": "P1"}, {"name": "W2", "purpose": "P2"}]
    )
    db.session.commit()
    assert QueryService.get_count(Widget) == 2


def test_get_latest_empty(db):  # noqa
    from app.widget.model import Widget
    assert QueryService.get_latest(Widget, "widget_id") is None


def test_get_latest_with_data(db):  # noqa
    from app.widget.model import Widget
    db.session.bulk_insert_mappings(
        Widget, [
            {"name": "First", "purpose": "P1"},
            {"name": "Second", "purpose": "P2"},
        ]
    )
    db.session.commit()
    latest = QueryService.get_latest(Widget, "widget_id")
    assert latest is not None
    assert latest["name"] == "Second"
    assert latest["purpose"] == "P2"
    assert "id" in latest


def test_get_resource_summary(db):  # noqa
    from app.widget.model import Widget
    from app.fizz.fizzbar.model import Fizzbar

    db.session.bulk_insert_mappings(
        Widget, [{"name": "W1", "purpose": "P1"}]
    )
    db.session.commit()

    resources = [
        {"name": "widget", "model": Widget, "id_col": "widget_id"},
        {"name": "fizzbar", "model": Fizzbar, "id_col": "fizzbar_id"},
    ]
    summary = QueryService.get_resource_summary(resources)
    assert summary["widget"]["count"] == 1
    assert summary["widget"]["latest"] is not None
    assert summary["fizzbar"]["count"] == 0
    assert summary["fizzbar"]["latest"] is None


def test_check_db_connectivity(app):  # noqa
    with app.app_context():
        assert QueryService.check_db_connectivity() is True
