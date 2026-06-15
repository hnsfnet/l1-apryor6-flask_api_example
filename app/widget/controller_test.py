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


def make_paginated_result(items, total=None, page=1, per_page=20):
    """Helper to build a paginated result dict matching QueryService output."""
    from math import ceil

    if total is None:
        total = len(items)
    pages = ceil(total / per_page) if total > 0 else 0
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": pages,
    }


class TestWidgetResource:
    @patch.object(
        WidgetService,
        "get_all",
        lambda query_params=None: make_paginated_result(
            [
                make_widget(123, name="Test Widget 1"),
                make_widget(456, name="Test Widget 2"),
            ]
        ),
    )
    def test_get(self, client: FlaskClient):  # noqa
        with client:
            response = client.get(f"/api/{BASE_ROUTE}/", follow_redirects=True)
            data = response.get_json()
            # Check pagination metadata
            assert data["total"] == 2
            assert data["page"] == 1
            assert data["per_page"] == 20
            assert data["pages"] == 1
            # Check items
            expected = WidgetSchema(many=True).dump(
                [
                    make_widget(123, name="Test Widget 1"),
                    make_widget(456, name="Test Widget 2"),
                ]
            )
            for item in data["items"]:
                assert item in expected

    @patch.object(
        WidgetService,
        "get_all",
        lambda query_params=None: make_paginated_result([], total=0),
    )
    def test_get_empty(self, client: FlaskClient):  # noqa
        with client:
            response = client.get(f"/api/{BASE_ROUTE}/", follow_redirects=True)
            data = response.get_json()
            assert data["total"] == 0
            assert data["items"] == []
            assert data["pages"] == 0

    @patch.object(
        WidgetService,
        "get_all",
        lambda query_params=None: make_paginated_result(
            [make_widget(1, name="Alpha")],
            total=50,
            page=3,
            per_page=10,
        ),
    )
    def test_get_with_pagination_params(self, client: FlaskClient):  # noqa
        with client:
            response = client.get(
                f"/api/{BASE_ROUTE}/?page=3&per_page=10", follow_redirects=True
            )
            data = response.get_json()
            assert data["page"] == 3
            assert data["per_page"] == 10
            assert data["total"] == 50
            assert data["pages"] == 5

    @patch.object(
        WidgetService,
        "get_all",
        lambda query_params=None: make_paginated_result(
            [make_widget(1, name="Match")],
            total=1,
        ),
    )
    def test_get_with_search(self, client: FlaskClient):  # noqa
        with client:
            response = client.get(
                f"/api/{BASE_ROUTE}/?search=Match", follow_redirects=True
            )
            data = response.get_json()
            assert data["total"] == 1
            assert len(data["items"]) == 1

    @patch.object(
        WidgetService,
        "get_all",
        lambda query_params=None: make_paginated_result(
            [make_widget(1, name="Zeta"), make_widget(2, name="Alpha")],
            total=2,
        ),
    )
    def test_get_with_sorting(self, client: FlaskClient):  # noqa
        with client:
            response = client.get(
                f"/api/{BASE_ROUTE}/?sort_by=name&sort_order=asc",
                follow_redirects=True,
            )
            data = response.get_json()
            assert data["total"] == 2

    def test_get_with_invalid_params_uses_defaults(self, client: FlaskClient):  # noqa
        """Invalid query params should not crash; defaults are applied."""
        with patch.object(
            WidgetService,
            "get_all",
            lambda query_params=None: make_paginated_result([]),
        ):
            with client:
                response = client.get(
                    f"/api/{BASE_ROUTE}/?page=abc&per_page=xyz&sort_by=bogus&sort_order=sideways",
                    follow_redirects=True,
                )
                data = response.get_json()
                assert data["page"] == 1
                assert data["per_page"] == 20

    @patch.object(
        WidgetService, "create", lambda create_request: Widget(**create_request)
    )
    def test_post(self, client: FlaskClient):  # noqa
        with client:

            payload = dict(name="Test widget", purpose="Test purpose")
            result = client.post(f"/api/{BASE_ROUTE}/", json=payload).get_json()
            expected = WidgetSchema().dump(
                Widget(name=payload["name"], purpose=payload["purpose"])
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
            expected = WidgetSchema().dump(
                Widget(widget_id=123, name="New Widget", purpose="New purpose")
            )
            assert result == expected
