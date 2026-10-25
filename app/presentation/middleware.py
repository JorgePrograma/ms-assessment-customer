import logging
import re
import time
from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse

from app.shared.api_response import ErrorBody, ErrorResponse
from app.shared.logging import request_id_ctx

logger = logging.getLogger("app.request")

REQUEST_ID_HEADER = "X-Request-ID"
_VALID_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


async def request_context_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    """Assigns a request id, logs the request outcome and turns unexpected errors into a 500 envelope."""
    incoming_id = request.headers.get(REQUEST_ID_HEADER, "")
    request_id = incoming_id if _VALID_REQUEST_ID.match(incoming_id) else uuid4().hex
    token = request_id_ctx.set(request_id)
    started_at = time.perf_counter()
    try:
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("Unhandled error on %s %s", request.method, request.url.path)
            response = JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=ErrorResponse(
                    error=ErrorBody(code="INTERNAL_ERROR", message="An unexpected error occurred")
                ).model_dump(),
            )
        duration_ms = (time.perf_counter() - started_at) * 1000
        logger.info("%s %s -> %s (%.1f ms)", request.method, request.url.path, response.status_code, duration_ms)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response
    finally:
        request_id_ctx.reset(token)
