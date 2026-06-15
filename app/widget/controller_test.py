from unittest.mock import patch
from flask.testing import FlaskClient

from app.test.fixtures import client, app  # noqa
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


# ---------------------------------------------------------------------------
# Batch create controller tests
# ---------------------------------------------------------------------------
class TestWidgetBatchCreate:
    @patch.object(
        WidgetService,
        "create_many",
        lambda items: (
            [
                make_widget(1, "W1", "P1"),
                make_widget(2, "W2", "P2"),
            ],
            [],
        ),
    )
    def test_batch_create_all_success(self, client: FlaskClient):  # noqa
        with client:
            payload = {
                "items": [
                    {"name": "W1", "purpose": "P1"},
                    {"name": "W2", "purpose": "P2"},
                ]
            }
            resp = client.post(f"/api/{BASE_ROUTE}/batch", json=payload)
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["total"] == 2
            assert data["succeeded"] == 2
            assert data["failed"] == 0
            assert len(data["successful_items"]) == 2
            assert data["failed_items"] == []

    @patch.object(
        WidgetService,
        "create_many",
        lambda items: (
            [make_widget(1, "Valid", "OK")],
            [{"index": 1, "error": "Missing required field: name"}],
        ),
    )
    def test_batch_create_partial_failure(self, client: FlaskClient):  # noqa
        with client:
            payload = {
                "items": [
                    {"name": "Valid", "purpose": "OK"},
                    {"purpose": "No name"},
                ]
            }
            resp = client.post(f"/api/{BASE_ROUTE}/batch", json=payload)
            assert resp.status_code == 207
            data = resp.get_json()
            assert data["total"] == 2
            assert data["succeeded"] == 1
            assert data["failed"] == 1
            assert len(data["successful_items"]) == 1
            assert len(data["failed_items"]) == 1
            assert data["failed_items"][0]["index"] == 1

    @patch.object(
        WidgetService,
        "create_many",
        lambda items: ([], []),
    )
    def test_batch_create_empty_list(self, client: FlaskClient):  # noqa
        with client:
            payload = {"items": []}
            resp = client.post(f"/api/{BASE_ROUTE}/batch", json=payload)
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["total"] == 0
            assert data["succeeded"] == 0
            assert data["failed"] == 0

    def test_batch_create_missing_items_key(self, client: FlaskClient):  # noqa
        with client:
            payload = {}
            resp = client.post(f"/api/{BASE_ROUTE}/batch", json=payload)
            # Should treat missing 'items' as empty list
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["total"] == 0

    def test_batch_create_invalid_items_type(self, client: FlaskClient):  # noqa
        with client:
            payload = {"items": "not a list"}
            resp = client.post(f"/api/{BASE_ROUTE}/batch", json=payload)
            assert resp.status_code == 400

    def test_batch_create_no_body(self, client: FlaskClient):  # noqa
        with client:
            resp = client.post(
                f"/api/{BASE_ROUTE}/batch",
                data="",
                content_type="application/json",
            )
            # Should handle gracefully
            assert resp.status_code in (200, 400)


# ---------------------------------------------------------------------------
# Batch delete controller tests
# ---------------------------------------------------------------------------
class TestWidgetBatchDelete:
    @patch.object(
        WidgetService,
        "delete_many",
        lambda ids: ([1, 2, 3], []),
    )
    def test_batch_delete_all_success(self, client: FlaskClient):  # noqa
        with client:
            payload = {"ids": [1, 2, 3]}
            resp = client.delete(f"/api/{BASE_ROUTE}/batch", json=payload)
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["total"] == 3
            assert data["succeeded"] == 3
            assert data["failed"] == 0
            assert data["successful_ids"] == [1, 2, 3]
            assert data["failed_items"] == []

    @patch.object(
        WidgetService,
        "delete_many",
        lambda ids: (
            [1],
            [{"id": 99, "error": "Not found"}],
        ),
    )
    def test_batch_delete_partial_not_found(self, client: FlaskClient):  # noqa
        with client:
            payload = {"ids": [1, 99]}
            resp = client.delete(f"/api/{BASE_ROUTE}/batch", json=payload)
            assert resp.status_code == 207
            data = resp.get_json()
            assert data["total"] == 2
            assert data["succeeded"] == 1
            assert data["failed"] == 1
            assert data["successful_ids"] == [1]
            assert len(data["failed_items"]) == 1
            assert data["failed_items"][0]["id"] == 99

    @patch.object(
        WidgetService,
        "delete_many",
        lambda ids: ([], []),
    )
    def test_batch_delete_empty_list(self, client: FlaskClient):  # noqa
        with client:
            payload = {"ids": []}
            resp = client.delete(f"/api/{BASE_ROUTE}/batch", json=payload)
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["total"] == 0

    @patch.object(
        WidgetService,
        "delete_many",
        lambda ids: (
            [1],
            [{"id": 1, "error": "Not found"}, {"id": 1, "error": "Not found"}],
        ),
    )
    def test_batch_delete_duplicate_ids(self, client: FlaskClient):  # noqa
        with client:
            payload = {"ids": [1, 1, 1]}
            resp = client.delete(f"/api/{BASE_ROUTE}/batch", json=payload)
            assert resp.status_code == 207
            data = resp.get_json()
            assert data["total"] == 3
            assert data["succeeded"] == 1
            assert data["failed"] == 2

    def test_batch_delete_missing_ids_key(self, client: FlaskClient):  # noqa
        with client:
            payload = {}
            resp = client.delete(f"/api/{BASE_ROUTE}/batch", json=payload)
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["total"] == 0

    def test_batch_delete_invalid_ids_type(self, client: FlaskClient):  # noqa
        with client:
            payload = {"ids": "not a list"}
            resp = client.delete(f"/api/{BASE_ROUTE}/batch", json=payload)
            assert resp.status_code == 400
