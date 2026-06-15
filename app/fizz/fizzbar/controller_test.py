from unittest.mock import patch
from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy

from app.test.fixtures import client, app, db  # noqa
from .service import FizzbarService
from .schema import FizzbarSchema
from .model import Fizzbar
from .interface import FizzbarInterface
from .. import BASE_ROUTE


def make_fizzbar(
    id: int = 123, name: str = "Test fizzbar", purpose: str = "Test purpose"
) -> Fizzbar:
    return Fizzbar(fizzbar_id=id, name=name, purpose=purpose)


class TestFizzbarResource:
    @patch.object(
        FizzbarService,
        "get_all",
        lambda: [
            make_fizzbar(123, name="Test Fizzbar 1"),
            make_fizzbar(456, name="Test Fizzbar 2"),
        ],
    )
    def test_get(self, client: FlaskClient):  # noqa
        with client:
            results = client.get(
                f"/api/{BASE_ROUTE}/fizzbar", follow_redirects=True
            ).get_json()
            expected = (
                FizzbarSchema(many=True)
                .dump(
                    [
                        make_fizzbar(123, name="Test Fizzbar 1"),
                        make_fizzbar(456, name="Test Fizzbar 2"),
                    ]
                )
                
            )
            for r in results:
                assert r in expected

    @patch.object(
        FizzbarService, "create", lambda create_request: Fizzbar(**create_request)
    )
    def test_post(self, client: FlaskClient):  # noqa
        with client:

            payload = dict(name="Test fizzbar", purpose="Test purpose")
            result = client.post(f"/api/{BASE_ROUTE}/fizzbar/", json=payload).get_json()
            expected = (
                FizzbarSchema()
                .dump(Fizzbar(name=payload["name"], purpose=payload["purpose"]))
                
            )
            assert result == expected


def fake_update(fizzbar: Fizzbar, changes: FizzbarInterface) -> Fizzbar:
    # To fake an update, just return a new object
    updated_Fizzbar = Fizzbar(
        fizzbar_id=fizzbar.fizzbar_id, name=changes["name"], purpose=changes["purpose"]
    )
    return updated_Fizzbar


class TestFizzbarIdResource:
    @patch.object(FizzbarService, "get_by_id", lambda id: make_fizzbar(id=id))
    def test_get(self, client: FlaskClient):  # noqa
        with client:
            result = client.get(f"/api/{BASE_ROUTE}/fizzbar/123").get_json()
            expected = Fizzbar(fizzbar_id=123)
            assert result["fizzbarId"] == expected.fizzbar_id

    @patch.object(FizzbarService, "delete_by_id", lambda id: id)
    def test_delete(self, client: FlaskClient):  # noqa
        with client:
            result = client.delete(f"/api/{BASE_ROUTE}/fizzbar/123").get_json()
            expected = dict(status="Success", id=123)
            assert result == expected

    @patch.object(FizzbarService, "get_by_id", lambda id: make_fizzbar(id=id))
    @patch.object(FizzbarService, "update", fake_update)
    def test_put(self, client: FlaskClient):  # noqa
        with client:
            result = client.put(
                f"/api/{BASE_ROUTE}/fizzbar/123",
                json={"name": "New Fizzbar", "purpose": "New purpose"},
            ).get_json()
            expected = (
                FizzbarSchema()
                .dump(
                    Fizzbar(fizzbar_id=123, name="New Fizzbar", purpose="New purpose")
                )

            )
            assert result == expected


class TestFizzbarErrorHandling:
    def test_get_not_found(self, client: FlaskClient, db: SQLAlchemy):  # noqa
        with client:
            resp = client.get(f"/api/{BASE_ROUTE}/fizzbar/999")
            assert resp.status_code == 404
            body = resp.get_json()
            assert body["error"] == "not_found"
            assert body["resource"] == "Fizzbar"
            assert body["resourceId"] == 999

    def test_delete_not_found(self, client: FlaskClient, db: SQLAlchemy):  # noqa
        with client:
            resp = client.delete(f"/api/{BASE_ROUTE}/fizzbar/999")
            assert resp.status_code == 404
            assert resp.get_json()["error"] == "not_found"

    def test_put_not_found(self, client: FlaskClient, db: SQLAlchemy):  # noqa
        with client:
            resp = client.put(
                f"/api/{BASE_ROUTE}/fizzbar/999",
                json={"name": "Nope", "purpose": "Nope"},
            )
            assert resp.status_code == 404
            assert resp.get_json()["error"] == "not_found"

    def test_post_missing_fields(self, client: FlaskClient):  # noqa
        with client:
            resp = client.post(f"/api/{BASE_ROUTE}/fizzbar/", json={})
            assert resp.status_code == 400
            body = resp.get_json()
            assert body["error"] == "validation_error"
            assert "name" in body["fields"]
            assert "purpose" in body["fields"]

    def test_put_empty_field(self, client: FlaskClient, db: SQLAlchemy):  # noqa
        db.session.add(make_fizzbar(id=1, name="Original", purpose="Original"))
        db.session.commit()
        with client:
            resp = client.put(f"/api/{BASE_ROUTE}/fizzbar/1", json={"name": ""})
            assert resp.status_code == 400
            assert resp.get_json()["error"] == "validation_error"
            assert Fizzbar.query.get(1).name == "Original"
