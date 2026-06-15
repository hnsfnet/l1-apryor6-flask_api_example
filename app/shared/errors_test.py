"""Tests for shared error utilities."""

import pytest
from app import create_app
from app.shared.errors import (
    ApiError,
    NotFoundException,
    ValidationError,
    error_response,
    register_error_handlers,
)


@pytest.fixture
def app():
    return create_app("test")


@pytest.fixture
def client(app):
    return app.test_client()


class TestApiError:
    def test_defaults(self):
        err = ApiError()
        assert err.status_code == 500
        assert err.error_type == "internal_error"
        assert err.message == "An unexpected error occurred"
        assert err.details is None

    def test_custom_message(self):
        err = ApiError("something broke", details={"key": "val"})
        assert err.message == "something broke"
        assert err.details == {"key": "val"}


class TestNotFoundException:
    def test_message(self):
        err = NotFoundException("Widget", 42)
        assert err.status_code == 404
        assert err.error_type == "not_found"
        assert "Widget" in err.message
        assert "42" in err.message
        assert err.details == {"resource": "Widget", "id": 42}


class TestValidationError:
    def test_message(self):
        err = ValidationError("bad input", details={"name": "required"})
        assert err.status_code == 400
        assert err.error_type == "validation_error"
        assert err.message == "bad input"
        assert err.details == {"name": "required"}


class TestErrorResponse:
    def test_response_shape(self, app):
        with app.app_context():
            err = NotFoundException("Fizzbar", 7)
            resp, code = error_response(err)
            assert code == 404
            data = resp.get_json()
            assert data["error"]["type"] == "not_found"
            assert data["error"]["details"]["resource"] == "Fizzbar"
            assert data["error"]["details"]["id"] == 7


class TestGlobalHandlers:
    def test_404_route(self, client):
        resp = client.get("/nonexistent-path-xyz")
        assert resp.status_code == 404
        body = resp.get_json()
        assert body["error"]["type"] == "not_found"
