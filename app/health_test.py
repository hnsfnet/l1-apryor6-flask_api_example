from flask.testing import FlaskClient

from app.test.fixtures import client, app, db  # noqa


class TestHealth:
    def test_health_reports_status_database_and_modules(
        self, client: FlaskClient, db  # noqa
    ):
        with client:
            result = client.get("/health").get_json()

            assert result["status"] == "healthy"
            assert result["database"] == "connected"
            # Module registration status helps diagnose env issues quickly.
            for name in ("widget", "fizzbar", "fizzbaz", "doodad", "whatsit"):
                assert name in result["modules"]
