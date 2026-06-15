import pytest
from app.test.fixtures import app, client, db  # noqa


class TestOverviewEndpoint:
    """Tests for GET /api/overview/"""

    def test_overview_returns_200(self, client, db):  # noqa
        resp = client.get("/api/overview/")
        assert resp.status_code == 200
        assert resp.is_json

    def test_overview_no_data(self, client, db):  # noqa
        """When DB is empty, all counts should be 0 and latest should be null."""
        resp = client.get("/api/overview/")
        data = resp.get_json()
        resources = data["resources"]

        for name in ("widget", "fizzbar", "fizzbaz", "doodad", "whatsit"):
            assert name in resources
            assert resources[name]["count"] == 0
            assert resources[name]["latest"] is None

    def test_overview_with_data(self, client, db):  # noqa
        """After seeding, counts should be >0 and latest should have id/name/purpose."""
        from app.widget.model import Widget
        from app.fizz.fizzbar.model import Fizzbar
        from app.fizz.fizzbaz.model import Fizzbaz
        from app.other_api.doodad.model import Doodad
        from app.other_api.whatsit.model import Whatsit

        things = [
            {"name": "Pizza Slicer", "purpose": "Cut pizza"},
            {"name": "Rolling Pin", "purpose": "Roll pizza"},
        ]
        for cls in (Widget, Fizzbar, Fizzbaz, Doodad, Whatsit):
            db.session.bulk_insert_mappings(cls, things)
        db.session.commit()

        resp = client.get("/api/overview/")
        data = resp.get_json()
        resources = data["resources"]

        for name in ("widget", "fizzbar", "fizzbaz", "doodad", "whatsit"):
            assert resources[name]["count"] == 2
            latest = resources[name]["latest"]
            assert latest is not None
            assert "id" in latest
            assert "name" in latest
            assert "purpose" in latest

    def test_overview_partial_data(self, client, db):  # noqa
        """Only some modules have data; others should show count=0 and latest=None."""
        from app.widget.model import Widget

        db.session.bulk_insert_mappings(
            Widget, [{"name": "Solo Widget", "purpose": "Testing partial"}]
        )
        db.session.commit()

        resp = client.get("/api/overview/")
        data = resp.get_json()
        resources = data["resources"]

        assert resources["widget"]["count"] == 1
        assert resources["widget"]["latest"] is not None
        assert resources["widget"]["latest"]["name"] == "Solo Widget"

        for name in ("fizzbar", "fizzbaz", "doodad", "whatsit"):
            assert resources[name]["count"] == 0
            assert resources[name]["latest"] is None


class TestHealthEndpoint:
    """Tests for GET /health"""

    def test_health_returns_200(self, client):  # noqa
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.is_json

    def test_health_structure(self, client):  # noqa
        resp = client.get("/health")
        data = resp.get_json()
        assert "status" in data
        assert "database" in data
        assert "modules" in data
        assert "namespaces" in data

    def test_health_db_connected(self, client):  # noqa
        resp = client.get("/health")
        data = resp.get_json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"

    def test_health_modules_listed(self, client):  # noqa
        resp = client.get("/health")
        data = resp.get_json()
        assert isinstance(data["modules"], list)
        assert isinstance(data["namespaces"], list)
