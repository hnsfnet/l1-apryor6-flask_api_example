"""Shared error types, request validation and a stable error response format.

Every error a client can trigger maps to an :class:`APIError` subclass. Each one
serialises to the same JSON envelope so callers never have to guess from the
status code alone::

    {
        "error": "not_found",            # stable machine readable code
        "message": "Widget with id 9 not found",
        "resource": "Widget",            # present for not-found errors
        "resourceId": 9,
        "fields": {"name": "..."}        # present for validation errors
    }

Handlers are registered once on the flask-restx ``Api`` in
:func:`register_error_handlers`, so individual controllers stay thin and new
modules get consistent behaviour for free.
"""

from typing import Any, Dict, Iterable, Mapping, Optional


class APIError(Exception):
    """Base class for errors that should be returned to the client as JSON."""

    status_code: int = 500
    error: str = "internal_error"

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code

    def to_dict(self) -> Dict[str, Any]:
        return {"error": self.error, "message": self.message}


class NotFoundError(APIError):
    """Raised when a requested resource does not exist."""

    status_code = 404
    error = "not_found"

    def __init__(self, resource: str, resource_id: Any):
        super().__init__(f"{resource} with id {resource_id} not found")
        self.resource = resource
        self.resource_id = resource_id

    def to_dict(self) -> Dict[str, Any]:
        body = super().to_dict()
        body["resource"] = self.resource
        body["resourceId"] = self.resource_id
        return body


class ValidationError(APIError):
    """Raised when an incoming request body fails validation."""

    status_code = 400
    error = "validation_error"

    def __init__(self, message: str, fields: Optional[Mapping[str, str]] = None):
        super().__init__(message)
        self.fields = dict(fields or {})

    def to_dict(self) -> Dict[str, Any]:
        body = super().to_dict()
        if self.fields:
            body["fields"] = self.fields
        return body


def _is_blank(value: Any) -> bool:
    """A value is blank if it is missing, ``None`` or an empty/whitespace string."""

    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    return False


def validate_required(attrs: Mapping[str, Any], required: Iterable[str]) -> None:
    """Ensure every field in ``required`` is present and non-empty.

    Use for create requests where the full set of core fields must be supplied.
    Raises :class:`ValidationError` listing every offending field so the caller
    fails before reaching the database layer.
    """

    bad = {
        field: "This field is required and cannot be empty"
        for field in required
        if _is_blank(attrs.get(field))
    }
    if bad:
        raise ValidationError(
            "Missing or empty required field(s): " + ", ".join(sorted(bad)),
            fields=bad,
        )


def validate_nonempty(attrs: Mapping[str, Any], fields: Iterable[str]) -> None:
    """Ensure listed fields are non-empty *when present*.

    Use for partial update requests: a field may be omitted, but if it is sent
    it must not be blank.
    """

    bad = {
        field: "This field cannot be empty"
        for field in fields
        if field in attrs and _is_blank(attrs.get(field))
    }
    if bad:
        raise ValidationError(
            "Field(s) cannot be empty: " + ", ".join(sorted(bad)),
            fields=bad,
        )


def register_error_handlers(api) -> None:
    """Register handlers that render :class:`APIError`s as the stable envelope."""

    @api.errorhandler(NotFoundError)
    def _handle_not_found(error: NotFoundError):
        return error.to_dict(), error.status_code

    @api.errorhandler(ValidationError)
    def _handle_validation(error: ValidationError):
        return error.to_dict(), error.status_code

    @api.errorhandler(APIError)
    def _handle_api_error(error: APIError):
        return error.to_dict(), error.status_code
