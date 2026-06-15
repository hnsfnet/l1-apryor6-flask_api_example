from unittest.mock import patch
from flask.testing import FlaskClient

from app.test.fixtures import client, app  # noqa
from .service import DoodadService
from .schema import DoodadSchema
from .model import Doodad
from .interface import DoodadInterface
from .. import BASE_ROUTE


def make_doodad(
    id: int = 123, name: str = "Test doodad", purpose: str = "Test purpose"
) -> Doodad:
    return Doodad(doodad_id=id, name=name, purpose=purpose)


class TestDoodadResource:
    @patch.object(
        DoodadService,
        "get_all",
        lambda: [
            make_doodad(123, name="Test Doodad 1"),
            make_doodad(456, name="Test Doodad 2"),
        ],
    )
    def test_get(self, client: FlaskClient):  # noqa
        with client:
            results = client.get(
                f"/api/{BASE_ROUTE}/doodad", follow_redirects=True
            ).get_json()
            expected = (
                DoodadSchema(many=True)
                .dump(
                    [
                        make_doodad(123, name="Test Doodad 1"),
                        make_doodad(456, name="Test Doodad 2"),
                    ]
                )

            )
            for r in results:
                assert r in expected

    @patch.object(
        DoodadService, "create", lambda create_request: Doodad(**create_request)
    )
    def test_post(self, client: FlaskClient):  # noqa
        with client:

            payload = dict(name="Test doodad", purpose="Test purpose")
            result = client.post(f"/api/{BASE_ROUTE}/doodad/", json=payload).get_json()
            expected = (
                DoodadSchema()
                .dump(Doodad(name=payload["name"], purpose=payload["purpose"]))

            )
            assert result == expected


def fake_update(doodad: Doodad, changes: DoodadInterface) -> Doodad:
    # To fake an update, just return a new object
    updated_Doodad = Doodad(
        doodad_id=doodad.doodad_id, name=changes["name"], purpose=changes["purpose"]
    )
    return updated_Doodad


class TestDoodadIdResource:
    @patch.object(DoodadService, "get_by_id", lambda id: make_doodad(id=id))
    def test_get(self, client: FlaskClient):  # noqa
        with client:
            result = client.get(f"/api/{BASE_ROUTE}/doodad/123").get_json()
            expected = Doodad(doodad_id=123)
            assert result["doodadId"] == expected.doodad_id

    @patch.object(DoodadService, "delete_by_id", lambda id: [id])
    def test_delete(self, client: FlaskClient):  # noqa
        with client:
            result = client.delete(f"/api/{BASE_ROUTE}/doodad/123").get_json()
            expected = dict(status="Success", id=[123])
            assert result == expected

    @patch.object(DoodadService, "get_by_id", lambda id: make_doodad(id=id))
    @patch.object(DoodadService, "update", fake_update)
    def test_put(self, client: FlaskClient):  # noqa
        with client:
            result = client.put(
                f"/api/{BASE_ROUTE}/doodad/123",
                json={"name": "New Doodad", "purpose": "New purpose"},
            ).get_json()
            expected = (
                DoodadSchema()
                .dump(Doodad(doodad_id=123, name="New Doodad", purpose="New purpose"))

            )
            assert result == expected


# ---------------------------------------------------------------------------
# Batch create controller tests
# ---------------------------------------------------------------------------
class TestDoodadBatchCreate:
    @patch.object(
        DoodadService,
        "create_many",
        lambda items: (
            [
                make_doodad(1, "D1", "P1"),
                make_doodad(2, "D2", "P2"),
            ],
            [],
        ),
    )
    def test_batch_create_all_success(self, client: FlaskClient):  # noqa
        with client:
            payload = {
                "items": [
                    {"name": "D1", "purpose": "P1"},
                    {"name": "D2", "purpose": "P2"},
                ]
            }
            resp = client.post(f"/api/{BASE_ROUTE}/doodad/batch", json=payload)
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["total"] == 2
            assert data["succeeded"] == 2
            assert data["failed"] == 0
            assert len(data["successful_items"]) == 2
            assert data["failed_items"] == []

    @patch.object(
        DoodadService,
        "create_many",
        lambda items: (
            [make_doodad(1, "Valid", "OK")],
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
            resp = client.post(f"/api/{BASE_ROUTE}/doodad/batch", json=payload)
            assert resp.status_code == 207
            data = resp.get_json()
            assert data["total"] == 2
            assert data["succeeded"] == 1
            assert data["failed"] == 1
            assert len(data["successful_items"]) == 1
            assert len(data["failed_items"]) == 1
            assert data["failed_items"][0]["index"] == 1

    @patch.object(
        DoodadService,
        "create_many",
        lambda items: ([], []),
    )
    def test_batch_create_empty_list(self, client: FlaskClient):  # noqa
        with client:
            payload = {"items": []}
            resp = client.post(f"/api/{BASE_ROUTE}/doodad/batch", json=payload)
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["total"] == 0
            assert data["succeeded"] == 0
            assert data["failed"] == 0

    def test_batch_create_missing_items_key(self, client: FlaskClient):  # noqa
        with client:
            payload = {}
            resp = client.post(f"/api/{BASE_ROUTE}/doodad/batch", json=payload)
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["total"] == 0

    def test_batch_create_invalid_items_type(self, client: FlaskClient):  # noqa
        with client:
            payload = {"items": "not a list"}
            resp = client.post(f"/api/{BASE_ROUTE}/doodad/batch", json=payload)
            assert resp.status_code == 400

    def test_batch_create_no_body(self, client: FlaskClient):  # noqa
        with client:
            resp = client.post(
                f"/api/{BASE_ROUTE}/doodad/batch",
                data="",
                content_type="application/json",
            )
            assert resp.status_code in (200, 400)


# ---------------------------------------------------------------------------
# Batch delete controller tests
# ---------------------------------------------------------------------------
class TestDoodadBatchDelete:
    @patch.object(
        DoodadService,
        "delete_many",
        lambda ids: ([1, 2, 3], []),
    )
    def test_batch_delete_all_success(self, client: FlaskClient):  # noqa
        with client:
            payload = {"ids": [1, 2, 3]}
            resp = client.delete(f"/api/{BASE_ROUTE}/doodad/batch", json=payload)
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["total"] == 3
            assert data["succeeded"] == 3
            assert data["failed"] == 0
            assert data["successful_ids"] == [1, 2, 3]
            assert data["failed_items"] == []

    @patch.object(
        DoodadService,
        "delete_many",
        lambda ids: (
            [1],
            [{"id": 99, "error": "Not found"}],
        ),
    )
    def test_batch_delete_partial_not_found(self, client: FlaskClient):  # noqa
        with client:
            payload = {"ids": [1, 99]}
            resp = client.delete(f"/api/{BASE_ROUTE}/doodad/batch", json=payload)
            assert resp.status_code == 207
            data = resp.get_json()
            assert data["total"] == 2
            assert data["succeeded"] == 1
            assert data["failed"] == 1
            assert data["successful_ids"] == [1]
            assert len(data["failed_items"]) == 1
            assert data["failed_items"][0]["id"] == 99

    @patch.object(
        DoodadService,
        "delete_many",
        lambda ids: ([], []),
    )
    def test_batch_delete_empty_list(self, client: FlaskClient):  # noqa
        with client:
            payload = {"ids": []}
            resp = client.delete(f"/api/{BASE_ROUTE}/doodad/batch", json=payload)
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["total"] == 0

    @patch.object(
        DoodadService,
        "delete_many",
        lambda ids: (
            [1],
            [{"id": 1, "error": "Not found"}, {"id": 1, "error": "Not found"}],
        ),
    )
    def test_batch_delete_duplicate_ids(self, client: FlaskClient):  # noqa
        with client:
            payload = {"ids": [1, 1, 1]}
            resp = client.delete(f"/api/{BASE_ROUTE}/doodad/batch", json=payload)
            assert resp.status_code == 207
            data = resp.get_json()
            assert data["total"] == 3
            assert data["succeeded"] == 1
            assert data["failed"] == 2

    def test_batch_delete_missing_ids_key(self, client: FlaskClient):  # noqa
        with client:
            payload = {}
            resp = client.delete(f"/api/{BASE_ROUTE}/doodad/batch", json=payload)
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["total"] == 0

    def test_batch_delete_invalid_ids_type(self, client: FlaskClient):  # noqa
        with client:
            payload = {"ids": "not a list"}
            resp = client.delete(f"/api/{BASE_ROUTE}/doodad/batch", json=payload)
            assert resp.status_code == 400
