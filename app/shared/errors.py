"""Unified error handling for the API.

Provides custom exception classes and helper functions so every endpoint
returns errors in the same JSON shape:

    {
        "error": {
            "type": "<error_type>",
            "message": "<human readable message>",
            "details": { ... }          # optional
        }
    }
"""

from flask import jsonify
from typing import Optional, Any


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------

class ApiError(Exception):
    """Base exception for all API errors."""

    status_code: int = 500
    error_type: str = "internal_error"

    def __init__(self, message: str = "An unexpected error occurred", details: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.details = details


class NotFoundException(ApiError):
    """Raised when a requested resource does not exist."""

    status_code = 404
    error_type = "not_found"

    def __init__(self, resource: str, resource_id: Any):
        message = f"{resource} with id {resource_id} not found"
        super().__init__(message=message, details={"resource": resource, "id": resource_id})


class ValidationError(ApiError):
    """Raised when request body fails validation."""

    status_code = 400
    error_type = "validation_error"

    def __init__(self, message: str = "Invalid request body", details: Optional[Any] = None):
        super().__init__(message=message, details=details)


# ---------------------------------------------------------------------------
# Response helpers
# ---------------------------------------------------------------------------

def error_response(error: ApiError):
    """Build a Flask JSON response from an ApiError."""
    body: dict = {
        "error": {
            "type": error.error_type,
            "message": error.message,
        }
    }
    if error.details is not None:
        body["error"]["details"] = error.details
    return jsonify(body), error.status_code


def register_error_handlers(app):
    """Register global error handlers on the Flask app."""

    @app.errorhandler(ApiError)
    def handle_api_error(error):
        return error_response(error)

    @app.errorhandler(404)
    def handle_404(error):
        return jsonify({
            "error": {
                "type": "not_found",
                "message": "The requested URL was not found on the server.",
            }
        }), 404

    @app.errorhandler(405)
    def handle_405(error):
        return jsonify({
            "error": {
                "type": "method_not_allowed",
                "message": "The HTTP method is not allowed for this endpoint.",
            }
        }), 405

    @app.errorhandler(500)
    def handle_500(error):
        return jsonify({
            "error": {
                "type": "internal_error",
                "message": "An unexpected internal error occurred.",
            }
        }), 500


# ---------------------------------------------------------------------------
# Swagger helpers
# ---------------------------------------------------------------------------

def register_error_models(api_ns):
    """Register standard error models on a flask-restx Namespace.

    Call this once per namespace so that ``@api.response(404, error_model)``
    and similar decorators reference a shared ``Error`` / ``ErrorDetail``
    model visible in the Swagger UI.
    """
    from flask_restx import fields

    error_detail_model = api_ns.model("ErrorDetail", {
        "resource": fields.String(description="Resource type, e.g. Widget"),
        "id": fields.Integer(description="Resource ID that was not found"),
    })

    error_model = api_ns.model("Error", {
        "type": fields.String(description="Error type identifier"),
        "message": fields.String(description="Human-readable error message"),
        "details": fields.Nested(error_detail_model, allow_null=True,
                                 description="Optional extra context"),
    })

    error_wrapper = api_ns.model("ErrorWrapper", {
        "error": fields.Nested(error_model),
    })

    return error_wrapper
