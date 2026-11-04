"""SCENTIQ Middleware and Global Exception Handlers.
Guarantees request ID correlation and consistent envelope formatting.
"""
import uuid
import time
from typing import Any, Dict, List, Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import request_id_ctx, logger
from app.core.errors import AppException, ErrorCode


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Assigns or propagates an X-Request-ID header on every HTTP request."""

    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("X-Request-ID")
        if not req_id:
            req_id = str(uuid.uuid4())

        # Set in contextvar for logging
        token = request_id_ctx.set(req_id)
        request.state.request_id = req_id

        start_time = time.time()
        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000
            response.headers["X-Request-ID"] = req_id
            response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
            return response
        finally:
            request_id_ctx.reset(token)


def create_error_envelope(
    request_id: str,
    status_code: int,
    errors: List[Dict[str, Any]],
) -> JSONResponse:
    """Builds standard SCENTIQ error envelope."""
    payload = {
        "data": None,
        "meta": {
            "request_id": request_id,
            "next_cursor": None,
        },
        "errors": errors,
    }
    return JSONResponse(status_code=status_code, content=payload)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    logger.warning(f"AppException [{exc.code}]: {exc.message} (field={exc.field})")
    errors = [{"code": exc.code.value, "message": exc.message, "field": exc.field}]
    if exc.details:
        errors.extend(exc.details)
    return create_error_envelope(req_id, exc.status_code, errors)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    errors = []
    for err in exc.errors():
        field_path = ".".join(str(p) for p in err.get("loc", []))
        errors.append({
            "code": ErrorCode.VALIDATION_ERROR.value,
            "message": err.get("msg", "Validation error"),
            "field": field_path,
        })
    logger.info(f"Validation error on {request.url.path}: {errors}")
    return create_error_envelope(req_id, 400, errors)


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    logger.exception(f"Unhandled error on {request.url.path}: {str(exc)}")
    errors = [{
        "code": ErrorCode.INTERNAL_ERROR.value,
        "message": "An unexpected error occurred. Please contact support with request ID.",
        "field": None,
    }]
    return create_error_envelope(req_id, 500, errors)
