from unittest.mock import patch
from flask.testing import FlaskClient

from app.test.fixtures import client, app  # noqa
from .service import FizzbazService
from .schema import FizzbazSchema
from .model import Fizzbaz
from .interface import FizzbazInterface
from .. import BASE_ROUTE


def make_fizzbaz(
    id: int = 123, name: str = "Test fizzbaz", purpose: str = "Test purpose"
) -> Fizzbaz:
    return Fizzbaz(fizzbaz_id=id, name=name, purpose=purpose)


class TestFizzbazResource:
    @patch.object(
        FizzbazService,
        "get_all",
        lambda: [
            make_fizzbaz(123, name="Test Fizzbaz 1"),
            make_fizzbaz(456, name="Test Fizzbaz 2"),
        ],
    )
    def test_get(self, client: FlaskClient):  # noqa
        with client:
            results = client.get(
                f"/api/{BASE_ROUTE}/fizzbaz", follow_redirects=True
            ).get_json()
            expected = (
                FizzbazSchema(many=True)
                .dump(
                    [
                        make_fizzbaz(123, name="Test Fizzbaz 1"),
                        make_fizzbaz(456, name="Test Fizzbaz 2"),
                    ]
                )

            )
            for r in results:
                assert r in expected

    @patch.object(
        FizzbazService, "create", lambda create_request: Fizzbaz(**create_request)
    )
    def test_post(self, client: FlaskClient):  # noqa
        with client:

            payload = dict(name="Test fizzbaz", purpose="Test purpose")
            result = client.post(f"/api/{BASE_ROUTE}/fizzbaz/", json=payload).get_json()
            expected = (
                FizzbazSchema()
                .dump(Fizzbaz(name=payload["name"], purpose=payload["purpose"]))

            )
            assert result == expected

    def test_post_missing_name(self, client: FlaskClient):  # noqa
        with client:
            payload = dict(purpose="Test purpose")
            resp = client.post(f"/api/{BASE_ROUTE}/fizzbaz/", json=payload)
            assert resp.status_code == 400
            body = resp.get_json()
            assert body["error"]["type"] == "validation_error"
            assert "name" in body["error"]["details"]

    def test_post_empty_name(self, client: FlaskClient):  # noqa
        with client:
            payload = dict(name="", purpose="Test purpose")
            resp = client.post(f"/api/{BASE_ROUTE}/fizzbaz/", json=payload)
            assert resp.status_code == 400
            body = resp.get_json()
            assert body["error"]["type"] == "validation_error"
            assert "name" in body["error"]["details"]

    def test_post_missing_purpose(self, client: FlaskClient):  # noqa
        with client:
            payload = dict(name="Test fizzbaz")
            resp = client.post(f"/api/{BASE_ROUTE}/fizzbaz/", json=payload)
            assert resp.status_code == 400
            body = resp.get_json()
            assert body["error"]["type"] == "validation_error"
            assert "purpose" in body["error"]["details"]


def fake_update(fizzbaz: Fizzbaz, changes: FizzbazInterface) -> Fizzbaz:
    # To fake an update, just return a new object
    updated_Fizzbaz = Fizzbaz(
        fizzbaz_id=fizzbaz.fizzbaz_id, name=changes["name"], purpose=changes["purpose"]
    )
    return updated_Fizzbaz


class TestFizzbazIdResource:
    @patch.object(FizzbazService, "get_by_id", lambda id: make_fizzbaz(id=id))
    def test_get(self, client: FlaskClient):  # noqa
        with client:
            result = client.get(f"/api/{BASE_ROUTE}/fizzbaz/123").get_json()
            expected = Fizzbaz(fizzbaz_id=123)
            assert result["fizzbazId"] == expected.fizzbaz_id

    @patch.object(FizzbazService, "get_by_id", lambda id: None)
    def test_get_not_found(self, client: FlaskClient):  # noqa
        with client:
            resp = client.get(f"/api/{BASE_ROUTE}/fizzbaz/999")
            assert resp.status_code == 404
            body = resp.get_json()
            assert body["error"]["type"] == "not_found"
            assert body["error"]["details"]["resource"] == "Fizzbaz"
            assert body["error"]["details"]["id"] == 999

    @patch.object(FizzbazService, "get_by_id", lambda id: make_fizzbaz(id=id))
    @patch.object(FizzbazService, "delete_by_id", lambda id: [id])
    def test_delete(self, client: FlaskClient):  # noqa
        with client:
            result = client.delete(f"/api/{BASE_ROUTE}/fizzbaz/123").get_json()
            expected = dict(status="Success", id=[123])
            assert result == expected

    @patch.object(FizzbazService, "get_by_id", lambda id: None)
    def test_delete_not_found(self, client: FlaskClient):  # noqa
        with client:
            resp = client.delete(f"/api/{BASE_ROUTE}/fizzbaz/999")
            assert resp.status_code == 404
            body = resp.get_json()
            assert body["error"]["type"] == "not_found"
            assert body["error"]["details"]["resource"] == "Fizzbaz"

    @patch.object(FizzbazService, "get_by_id", lambda id: make_fizzbaz(id=id))
    @patch.object(FizzbazService, "update", fake_update)
    def test_put(self, client: FlaskClient):  # noqa
        with client:
            result = client.put(
                f"/api/{BASE_ROUTE}/fizzbaz/123",
                json={"name": "New Fizzbaz", "purpose": "New purpose"},
            ).get_json()
            expected = (
                FizzbazSchema()
                .dump(
                    Fizzbaz(fizzbaz_id=123, name="New Fizzbaz", purpose="New purpose")
                )

            )
            assert result == expected

    @patch.object(FizzbazService, "get_by_id", lambda id: None)
    def test_put_not_found(self, client: FlaskClient):  # noqa
        with client:
            resp = client.put(
                f"/api/{BASE_ROUTE}/fizzbaz/999",
                json={"name": "New Fizzbaz", "purpose": "New purpose"},
            )
            assert resp.status_code == 404
            body = resp.get_json()
            assert body["error"]["type"] == "not_found"
            assert body["error"]["details"]["resource"] == "Fizzbaz"
