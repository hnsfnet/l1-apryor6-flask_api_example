from unittest.mock import patch
from flask.testing import FlaskClient

from app.test.fixtures import client, app  # noqa
from .service import FizzbarService
from .schema import FizzbarSchema
from .model import Fizzbar
from .interface import FizzbarInterface
from .. import BASE_ROUTE


def make_fizzbar(
    id: int = 123, name: str = "Test fizzbar", purpose: str = "Test purpose"
) -> Fizzbar:
    return Fizzbar(fizzbar_id=id, name=name, purpose=purpose)


def make_paginated_result(items, total=None, page=1, per_page=20):
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


class TestFizzbarResource:
    @patch.object(
        FizzbarService,
        "get_all",
        lambda query_params=None: make_paginated_result(
            [
                make_fizzbar(123, name="Test Fizzbar 1"),
                make_fizzbar(456, name="Test Fizzbar 2"),
            ]
        ),
    )
    def test_get(self, client: FlaskClient):  # noqa
        with client:
            response = client.get(
                f"/api/{BASE_ROUTE}/fizzbar/", follow_redirects=True
            )
            data = response.get_json()
            assert data["total"] == 2
            assert data["page"] == 1
            assert data["per_page"] == 20
            assert data["pages"] == 1
            expected = FizzbarSchema(many=True).dump(
                [
                    make_fizzbar(123, name="Test Fizzbar 1"),
                    make_fizzbar(456, name="Test Fizzbar 2"),
                ]
            )
            for item in data["items"]:
                assert item in expected

    @patch.object(
        FizzbarService,
        "get_all",
        lambda query_params=None: make_paginated_result([], total=0),
    )
    def test_get_empty(self, client: FlaskClient):  # noqa
        with client:
            response = client.get(
                f"/api/{BASE_ROUTE}/fizzbar/", follow_redirects=True
            )
            data = response.get_json()
            assert data["total"] == 0
            assert data["items"] == []
            assert data["pages"] == 0

    @patch.object(
        FizzbarService,
        "get_all",
        lambda query_params=None: make_paginated_result(
            [make_fizzbar(1, name="Alpha")],
            total=50,
            page=3,
            per_page=10,
        ),
    )
    def test_get_with_pagination_params(self, client: FlaskClient):  # noqa
        with client:
            response = client.get(
                f"/api/{BASE_ROUTE}/fizzbar/?page=3&per_page=10",
                follow_redirects=True,
            )
            data = response.get_json()
            assert data["page"] == 3
            assert data["per_page"] == 10
            assert data["total"] == 50
            assert data["pages"] == 5

    @patch.object(
        FizzbarService,
        "get_all",
        lambda query_params=None: make_paginated_result(
            [make_fizzbar(1, name="Match")],
            total=1,
        ),
    )
    def test_get_with_search(self, client: FlaskClient):  # noqa
        with client:
            response = client.get(
                f"/api/{BASE_ROUTE}/fizzbar/?search=Match",
                follow_redirects=True,
            )
            data = response.get_json()
            assert data["total"] == 1

    def test_get_with_invalid_params_uses_defaults(self, client: FlaskClient):  # noqa
        with patch.object(
            FizzbarService,
            "get_all",
            lambda query_params=None: make_paginated_result([]),
        ):
            with client:
                response = client.get(
                    f"/api/{BASE_ROUTE}/fizzbar/?page=abc&sort_by=bogus",
                    follow_redirects=True,
                )
                data = response.get_json()
                assert data["page"] == 1
                assert data["per_page"] == 20

    @patch.object(
        FizzbarService, "create", lambda create_request: Fizzbar(**create_request)
    )
    def test_post(self, client: FlaskClient):  # noqa
        with client:

            payload = dict(name="Test fizzbar", purpose="Test purpose")
            result = client.post(f"/api/{BASE_ROUTE}/fizzbar/", json=payload).get_json()
            expected = FizzbarSchema().dump(
                Fizzbar(name=payload["name"], purpose=payload["purpose"])
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

    @patch.object(FizzbarService, "delete_by_id", lambda id: [id])
    def test_delete(self, client: FlaskClient):  # noqa
        with client:
            result = client.delete(f"/api/{BASE_ROUTE}/fizzbar/123").get_json()
            expected = dict(status="Success", id=[123])
            assert result == expected

    @patch.object(FizzbarService, "get_by_id", lambda id: make_fizzbar(id=id))
    @patch.object(FizzbarService, "update", fake_update)
    def test_put(self, client: FlaskClient):  # noqa
        with client:
            result = client.put(
                f"/api/{BASE_ROUTE}/fizzbar/123",
                json={"name": "New Fizzbar", "purpose": "New purpose"},
            ).get_json()
            expected = FizzbarSchema().dump(
                Fizzbar(fizzbar_id=123, name="New Fizzbar", purpose="New purpose")
            )
            assert result == expected
