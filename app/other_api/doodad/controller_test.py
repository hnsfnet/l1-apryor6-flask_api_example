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


def fake_create_bulk(items):
    # Two valid doodads created, one rejected for a missing field.
    return dict(
        succeeded=[
            make_doodad(1, name="Bulk 1"),
            make_doodad(2, name="Bulk 2"),
        ],
        failed=[
            dict(index=2, item=dict(name="No purpose"),
                 error="Missing required field(s): purpose")
        ],
        success_count=2,
        failure_count=1,
    )


def fake_delete_bulk(ids):
    return dict(
        requested=[1, 2, 99, 1],
        deleted=[1, 2],
        not_found=[99, 1],
        success_count=2,
        failure_count=2,
    )


class TestDoodadBulkResource:
    @patch.object(DoodadService, "create_bulk", fake_create_bulk)
    def test_bulk_post(self, client: FlaskClient):  # noqa
        with client:
            payload = dict(
                items=[
                    dict(name="Bulk 1", purpose="p1"),
                    dict(name="Bulk 2", purpose="p2"),
                    dict(name="No purpose"),
                ]
            )
            result = client.post(
                f"/api/{BASE_ROUTE}/doodad/bulk", json=payload
            ).get_json()

            assert result["success_count"] == 2
            assert result["failure_count"] == 1
            assert len(result["succeeded"]) == 2
            assert {d["name"] for d in result["succeeded"]} == {"Bulk 1", "Bulk 2"}
            assert result["failed"][0]["index"] == 2
            assert "purpose" in result["failed"][0]["error"]

    def test_bulk_post_empty(self, client: FlaskClient):  # noqa
        with patch.object(
            DoodadService,
            "create_bulk",
            lambda items: dict(
                succeeded=[], failed=[], success_count=0, failure_count=0
            ),
        ):
            with client:
                result = client.post(
                    f"/api/{BASE_ROUTE}/doodad/bulk", json=dict(items=[])
                ).get_json()
                assert result["success_count"] == 0
                assert result["failure_count"] == 0
                assert result["succeeded"] == []
                assert result["failed"] == []

    @patch.object(DoodadService, "delete_bulk", fake_delete_bulk)
    def test_bulk_delete(self, client: FlaskClient):  # noqa
        with client:
            result = client.delete(
                f"/api/{BASE_ROUTE}/doodad/bulk", json=dict(ids=[1, 2, 99, 1])
            ).get_json()

            assert result["deleted"] == [1, 2]
            assert result["not_found"] == [99, 1]
            assert result["success_count"] == 2
            assert result["failure_count"] == 2
