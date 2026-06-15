from unittest.mock import patch
from flask.testing import FlaskClient

from app.test.fixtures import client, app  # noqa
from .service import OverviewService
from . import BASE_ROUTE


FAKE_OVERVIEW = {
    "total": 3,
    "resources": {
        "widget": {"count": 2, "latest": {"id": 2, "name": "W2", "purpose": "wp"}},
        "fizzbar": {"count": 1, "latest": {"id": 1, "name": "FB", "purpose": "fp"}},
        "fizzbaz": {"count": 0, "latest": None},
        "doodad": {"count": 0, "latest": None},
        "whatsit": {"count": 0, "latest": None},
    },
}


class TestOverviewResource:
    @patch.object(OverviewService, "get_overview", lambda: FAKE_OVERVIEW)
    def test_get(self, client: FlaskClient):  # noqa
        with client:
            result = client.get(
                f"/api/{BASE_ROUTE}/", follow_redirects=True
            ).get_json()
            assert result == FAKE_OVERVIEW

    @patch.object(
        OverviewService,
        "get_overview",
        lambda: {
            "total": 0,
            "resources": {"widget": {"count": 0, "latest": None}},
        },
    )
    def test_get_when_empty(self, client: FlaskClient):  # noqa
        with client:
            result = client.get(
                f"/api/{BASE_ROUTE}/", follow_redirects=True
            ).get_json()
            assert result["total"] == 0
            # Empty state is a single null, easy for the frontend to handle.
            assert result["resources"]["widget"]["latest"] is None
