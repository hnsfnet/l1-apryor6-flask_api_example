from app.test.fixtures import app, db  # noqa
from app.widget.model import Widget
from app.fizz.fizzbar.model import Fizzbar
from app.fizz.fizzbaz.model import Fizzbaz
from app.other_api.doodad.model import Doodad
from app.other_api.whatsit.model import Whatsit
from .service import OverviewService


ALL_RESOURCES = ["widget", "fizzbar", "fizzbaz", "doodad", "whatsit"]


def test_module_names_lists_all_registered_resources():
    assert OverviewService.module_names() == ALL_RESOURCES


def test_get_overview_with_no_data(db):  # noqa
    overview = OverviewService.get_overview()

    assert overview["total"] == 0
    assert set(overview["resources"].keys()) == set(ALL_RESOURCES)
    # Empty DB must still return a clean, consistent shape (no errors/nulls).
    for name in ALL_RESOURCES:
        assert overview["resources"][name] == {"count": 0, "latest": None}


def test_get_overview_with_data(db):  # noqa
    db.session.add(Widget(name="W1", purpose="wp"))
    db.session.add(Fizzbar(name="FB1", purpose="fbp"))
    db.session.add(Fizzbaz(name="FBZ1", purpose="fbzp"))
    db.session.add(Doodad(name="D1", purpose="dp"))
    db.session.add(Whatsit(name="WH1", purpose="whp"))
    db.session.commit()

    overview = OverviewService.get_overview()

    assert overview["total"] == 5
    for name in ALL_RESOURCES:
        summary = overview["resources"][name]
        assert summary["count"] == 1
        assert summary["latest"] is not None
        assert set(summary["latest"].keys()) == {"id", "name", "purpose"}
    assert overview["resources"]["widget"]["latest"]["name"] == "W1"
    assert overview["resources"]["whatsit"]["latest"]["purpose"] == "whp"


def test_get_overview_returns_most_recent_record(db):  # noqa
    db.session.add(Widget(name="Older", purpose="p"))
    db.session.add(Widget(name="Newer", purpose="p"))
    db.session.commit()

    overview = OverviewService.get_overview()

    assert overview["resources"]["widget"]["count"] == 2
    # Highest primary key == most recently inserted row.
    assert overview["resources"]["widget"]["latest"]["name"] == "Newer"


def test_get_overview_with_partial_data(db):  # noqa
    # Only some modules have rows; the rest must report a clean empty state
    # rather than failing or producing inconsistent output.
    db.session.add(Widget(name="W1", purpose="wp"))
    db.session.add(Widget(name="W2", purpose="wp2"))
    db.session.add(Doodad(name="D1", purpose="dp"))
    db.session.commit()

    overview = OverviewService.get_overview()

    assert overview["total"] == 3
    assert overview["resources"]["widget"]["count"] == 2
    assert overview["resources"]["widget"]["latest"]["name"] == "W2"
    assert overview["resources"]["doodad"]["count"] == 1
    assert overview["resources"]["doodad"]["latest"]["name"] == "D1"
    for empty in ("fizzbar", "fizzbaz", "whatsit"):
        assert overview["resources"][empty] == {"count": 0, "latest": None}
