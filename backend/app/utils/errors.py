"""Unified business exception classes and FastAPI exception handlers."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


# ---------------------------------------------------------------------------
# Base business exception
# ---------------------------------------------------------------------------

class AppError(Exception):
    """Base class for all business exceptions."""

    status_code: int = 500
    message: str = "Internal server error"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.__class__.message
        super().__init__(self.message)


# ---------------------------------------------------------------------------
# Concrete exception types
# ---------------------------------------------------------------------------

class ValidationError(AppError):
    """Request parameter validation failed."""

    status_code = 400
    message = "Request parameter validation failed"


class AuthenticationError(AppError):
    """Not authenticated or token expired."""

    status_code = 401
    message = "Not authenticated or token expired"


class ForbiddenError(AppError):
    """No permission to access this resource."""

    status_code = 403
    message = "No permission"


class NotFoundError(AppError):
    """Resource not found."""

    status_code = 404
    message = "Resource not found"


class ConflictError(AppError):
    """Resource conflict (e.g., duplicate creation)."""

    status_code = 409
    message = "Resource conflict"


class AIServiceError(AppError):
    """AI service call failed."""

    status_code = 502
    message = "AI service call failed"


class ExternalServiceError(AppError):
    """External service unavailable."""

    status_code = 503
    message = "External service unavailable"


# ---------------------------------------------------------------------------
# FastAPI exception handler
# ---------------------------------------------------------------------------

async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    """Return a standardised JSON envelope for business exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": exc.message,
            "data": None,
        },
    )


# ---------------------------------------------------------------------------
# Helper to register all handlers on a FastAPI app
# ---------------------------------------------------------------------------

_EXCEPTION_CLASSES: list[type[AppError]] = [
    ValidationError,
    AuthenticationError,
    ForbiddenError,
    NotFoundError,
    ConflictError,
    AIServiceError,
    ExternalServiceError,
]


def register_exception_handlers(app: object) -> None:
    """Register the unified exception handler for every business exception type.

    Also registers a catch-all handler for the base ``AppError`` so that any
    future subclass is automatically covered.
    """
    for exc_cls in _EXCEPTION_CLASSES:
        app.exception_handler(exc_cls)(app_error_handler)  # type: ignore[arg-type]
    # Catch-all for the base class (covers future subclasses)
    app.exception_handler(AppError)(app_error_handler)  # type: ignore[arg-type]
