from app.test.fixtures import app, db  # noqa
from app.widget.model import Widget
from .service import QueryService


def test_execute():
    result = QueryService.execute("a complicated query")

    assert result == "Success"


def test_summarize_empty(db):  # noqa
    summary = QueryService.summarize(Widget)

    assert summary == {"count": 0, "latest": None}


def test_summarize_with_data(db):  # noqa
    db.session.add(Widget(name="First", purpose="p1"))
    db.session.add(Widget(name="Second", purpose="p2"))
    db.session.commit()

    summary = QueryService.summarize(Widget)

    assert summary["count"] == 2
    # Latest record reflects the highest primary key.
    assert summary["latest"]["name"] == "Second"
    assert summary["latest"]["purpose"] == "p2"
    assert isinstance(summary["latest"]["id"], int)
