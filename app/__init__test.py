from app.test.fixtures import app, client  # noqa


def test_app_creates(app):  # noqa
    assert app


def test_app_healthy(app, client):  # noqa
    with client:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.is_json
        assert resp.json["status"] == "healthy"
        assert resp.json["database"] in ("connected", "disconnected")
        assert "widget" in resp.json["modules"]
