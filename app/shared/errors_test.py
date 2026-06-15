import pytest

from app.shared.errors import (
    APIError,
    NotFoundError,
    ValidationError,
    validate_nonempty,
    validate_required,
)


def test_not_found_to_dict():
    err = NotFoundError("Widget", 7)
    assert err.status_code == 404
    body = err.to_dict()
    assert body == {
        "error": "not_found",
        "message": "Widget with id 7 not found",
        "resource": "Widget",
        "resourceId": 7,
    }


def test_validation_error_to_dict_includes_fields():
    err = ValidationError("bad", fields={"name": "required"})
    assert err.status_code == 400
    body = err.to_dict()
    assert body["error"] == "validation_error"
    assert body["fields"] == {"name": "required"}


def test_validation_error_without_fields_omits_key():
    body = ValidationError("bad").to_dict()
    assert "fields" not in body


def test_base_api_error_defaults():
    err = APIError("boom")
    assert err.status_code == 500
    assert err.to_dict() == {"error": "internal_error", "message": "boom"}


def test_validate_required_passes_when_present():
    validate_required({"name": "a", "purpose": "b"}, ("name", "purpose"))


@pytest.mark.parametrize(
    "attrs", [{}, {"name": "a"}, {"name": "a", "purpose": ""}, {"name": "  "}]
)
def test_validate_required_rejects_missing_or_blank(attrs):
    with pytest.raises(ValidationError):
        validate_required(attrs, ("name", "purpose"))


def test_validate_nonempty_allows_absent_field():
    # purpose omitted entirely is fine for a partial update
    validate_nonempty({"name": "a"}, ("name", "purpose"))


def test_validate_nonempty_rejects_present_but_blank():
    with pytest.raises(ValidationError) as excinfo:
        validate_nonempty({"name": ""}, ("name", "purpose"))
    assert "name" in excinfo.value.fields
