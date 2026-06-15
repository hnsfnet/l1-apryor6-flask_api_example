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


class TestFizzbazResource:
    @patch.object(
        FizzbazService,
        "get_all",
        lambda query_params=None: make_paginated_result(
            [
                make_fizzbaz(123, name="Test Fizzbaz 1"),
                make_fizzbaz(456, name="Test Fizzbaz 2"),
            ]
        ),
    )
    def test_get(self, client: FlaskClient):  # noqa
        with client:
            response = client.get(
                f"/api/{BASE_ROUTE}/fizzbaz/", follow_redirects=True
            )
            data = response.get_json()
            assert data["total"] == 2
            assert data["page"] == 1
            assert data["per_page"] == 20
            assert data["pages"] == 1
            expected = FizzbazSchema(many=True).dump(
                [
                    make_fizzbaz(123, name="Test Fizzbaz 1"),
                    make_fizzbaz(456, name="Test Fizzbaz 2"),
                ]
            )
            for item in data["items"]:
                assert item in expected

    @patch.object(
        FizzbazService,
        "get_all",
        lambda query_params=None: make_paginated_result([], total=0),
    )
    def test_get_empty(self, client: FlaskClient):  # noqa
        with client:
            response = client.get(
                f"/api/{BASE_ROUTE}/fizzbaz/", follow_redirects=True
            )
            data = response.get_json()
            assert data["total"] == 0
            assert data["items"] == []
            assert data["pages"] == 0

    @patch.object(
        FizzbazService,
        "get_all",
        lambda query_params=None: make_paginated_result(
            [make_fizzbaz(1, name="Alpha")],
            total=50,
            page=3,
            per_page=10,
        ),
    )
    def test_get_with_pagination_params(self, client: FlaskClient):  # noqa
        with client:
            response = client.get(
                f"/api/{BASE_ROUTE}/fizzbaz/?page=3&per_page=10",
                follow_redirects=True,
            )
            data = response.get_json()
            assert data["page"] == 3
            assert data["per_page"] == 10
            assert data["total"] == 50
            assert data["pages"] == 5

    @patch.object(
        FizzbazService,
        "get_all",
        lambda query_params=None: make_paginated_result(
            [make_fizzbaz(1, name="Match")],
            total=1,
        ),
    )
    def test_get_with_search(self, client: FlaskClient):  # noqa
        with client:
            response = client.get(
                f"/api/{BASE_ROUTE}/fizzbaz/?search=Match",
                follow_redirects=True,
            )
            data = response.get_json()
            assert data["total"] == 1

    def test_get_with_invalid_params_uses_defaults(self, client: FlaskClient):  # noqa
        with patch.object(
            FizzbazService,
            "get_all",
            lambda query_params=None: make_paginated_result([]),
        ):
            with client:
                response = client.get(
                    f"/api/{BASE_ROUTE}/fizzbaz/?page=abc&sort_by=bogus",
                    follow_redirects=True,
                )
                data = response.get_json()
                assert data["page"] == 1
                assert data["per_page"] == 20

    @patch.object(
        FizzbazService, "create", lambda create_request: Fizzbaz(**create_request)
    )
    def test_post(self, client: FlaskClient):  # noqa
        with client:

            payload = dict(name="Test fizzbaz", purpose="Test purpose")
            result = client.post(f"/api/{BASE_ROUTE}/fizzbaz/", json=payload).get_json()
            expected = FizzbazSchema().dump(
                Fizzbaz(name=payload["name"], purpose=payload["purpose"])
            )
            assert result == expected


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

    @patch.object(FizzbazService, "delete_by_id", lambda id: [id])
    def test_delete(self, client: FlaskClient):  # noqa
        with client:
            result = client.delete(f"/api/{BASE_ROUTE}/fizzbaz/123").get_json()
            expected = dict(status="Success", id=[123])
            assert result == expected

    @patch.object(FizzbazService, "get_by_id", lambda id: make_fizzbaz(id=id))
    @patch.object(FizzbazService, "update", fake_update)
    def test_put(self, client: FlaskClient):  # noqa
        with client:
            result = client.put(
                f"/api/{BASE_ROUTE}/fizzbaz/123",
                json={"name": "New Fizzbaz", "purpose": "New purpose"},
            ).get_json()
            expected = FizzbazSchema().dump(
                Fizzbaz(fizzbaz_id=123, name="New Fizzbaz", purpose="New purpose")
            )
            assert result == expected
