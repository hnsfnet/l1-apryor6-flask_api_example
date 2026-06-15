from unittest.mock import patch
from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy

from app.test.fixtures import client, app, db  # noqa
from .service import WidgetService
from .schema import WidgetSchema
from .model import Widget
from .interface import WidgetInterface
from . import BASE_ROUTE


def make_widget(
    id: int = 123, name: str = "Test widget", purpose: str = "Test purpose"
) -> Widget:
    return Widget(widget_id=id, name=name, purpose=purpose)


class TestWidgetResource:
    @patch.object(
        WidgetService,
        "get_all",
        lambda: [
            make_widget(123, name="Test Widget 1"),
            make_widget(456, name="Test Widget 2"),
        ],
    )
    def test_get(self, client: FlaskClient):  # noqa
        with client:
            results = client.get(f"/api/{BASE_ROUTE}", follow_redirects=True).get_json()
            expected = (
                WidgetSchema(many=True)
                .dump(
                    [
                        make_widget(123, name="Test Widget 1"),
                        make_widget(456, name="Test Widget 2"),
                    ]
                )
                
            )
            for r in results:
                assert r in expected

    @patch.object(
        WidgetService, "create", lambda create_request: Widget(**create_request)
    )
    def test_post(self, client: FlaskClient):  # noqa
        with client:

            payload = dict(name="Test widget", purpose="Test purpose")
            result = client.post(f"/api/{BASE_ROUTE}/", json=payload).get_json()
            expected = (
                WidgetSchema()
                .dump(Widget(name=payload["name"], purpose=payload["purpose"]))
                
            )
            assert result == expected


def fake_update(widget: Widget, changes: WidgetInterface) -> Widget:
    # To fake an update, just return a new object
    updated_Widget = Widget(
        widget_id=widget.widget_id, name=changes["name"], purpose=changes["purpose"]
    )
    return updated_Widget


class TestWidgetIdResource:
    @patch.object(WidgetService, "get_by_id", lambda id: make_widget(id=id))
    def test_get(self, client: FlaskClient):  # noqa
        with client:
            result = client.get(f"/api/{BASE_ROUTE}/123").get_json()
            expected = make_widget(id=123)
            print(f"result = ", result)
            assert result["widgetId"] == expected.widget_id

    @patch.object(WidgetService, "delete_by_id", lambda id: id)
    def test_delete(self, client: FlaskClient):  # noqa
        with client:
            result = client.delete(f"/api/{BASE_ROUTE}/123").get_json()
            expected = dict(status="Success", id=123)
            assert result == expected

    @patch.object(WidgetService, "get_by_id", lambda id: make_widget(id=id))
    @patch.object(WidgetService, "update", fake_update)
    def test_put(self, client: FlaskClient):  # noqa
        with client:
            result = client.put(
                f"/api/{BASE_ROUTE}/123",
                json={"name": "New Widget", "purpose": "New purpose"},
            ).get_json()
            expected = (
                WidgetSchema()
                .dump(Widget(widget_id=123, name="New Widget", purpose="New purpose"))

            )
            assert result == expected


class TestWidgetErrorHandling:
    def test_get_not_found(self, client: FlaskClient, db: SQLAlchemy):  # noqa
        with client:
            resp = client.get(f"/api/{BASE_ROUTE}/999")
            assert resp.status_code == 404
            body = resp.get_json()
            assert body["error"] == "not_found"
            assert body["resource"] == "Widget"
            assert body["resourceId"] == 999

    def test_delete_not_found(self, client: FlaskClient, db: SQLAlchemy):  # noqa
        with client:
            resp = client.delete(f"/api/{BASE_ROUTE}/999")
            assert resp.status_code == 404
            assert resp.get_json()["error"] == "not_found"

    def test_put_not_found(self, client: FlaskClient, db: SQLAlchemy):  # noqa
        with client:
            resp = client.put(
                f"/api/{BASE_ROUTE}/999",
                json={"name": "Nope", "purpose": "Nope"},
            )
            assert resp.status_code == 404
            assert resp.get_json()["error"] == "not_found"

    def test_post_missing_fields(self, client: FlaskClient):  # noqa
        with client:
            resp = client.post(f"/api/{BASE_ROUTE}/", json={})
            assert resp.status_code == 400
            body = resp.get_json()
            assert body["error"] == "validation_error"
            assert "name" in body["fields"]
            assert "purpose" in body["fields"]

    def test_post_empty_field(self, client: FlaskClient):  # noqa
        with client:
            resp = client.post(
                f"/api/{BASE_ROUTE}/", json={"name": "   ", "purpose": "ok"}
            )
            assert resp.status_code == 400
            body = resp.get_json()
            assert body["error"] == "validation_error"
            assert "name" in body["fields"]
            assert "purpose" not in body["fields"]

    def test_put_empty_field(self, client: FlaskClient, db: SQLAlchemy):  # noqa
        db.session.add(make_widget(id=1, name="Original", purpose="Original"))
        db.session.commit()
        with client:
            resp = client.put(f"/api/{BASE_ROUTE}/1", json={"name": ""})
            assert resp.status_code == 400
            assert resp.get_json()["error"] == "validation_error"
            # the original record must be left untouched
            assert Widget.query.get(1).name == "Original"
