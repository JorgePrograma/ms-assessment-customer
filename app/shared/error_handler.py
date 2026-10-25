import logging
from http import HTTPStatus

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.domain.errors import DomainError, ValidationError
from app.shared.api_response import ErrorBody, ErrorDetail, ErrorResponse

logger = logging.getLogger(__name__)

_REQUEST_PARTS = {"body", "query", "path", "header", "cookie"}


def _error_response(status_code: int, error: ErrorBody) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=ErrorResponse(error=error).model_dump())


async def domain_error_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, DomainError)
    logger.warning("Business rule violated: %s on %s %s", exc.code, request.method, request.url.path)
    details = [ErrorDetail(field=exc.field, message=exc.message)] if isinstance(exc, ValidationError) else None
    return _error_response(exc.status_code, ErrorBody(code=exc.code, message=exc.message, details=details))


async def request_validation_error_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    details = []
    for error in exc.errors():
        location = [str(part) for part in error["loc"] if part not in _REQUEST_PARTS]
        details.append(ErrorDetail(field=".".join(location) or None, message=error["msg"]))
    return _error_response(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        ErrorBody(code="VALIDATION_ERROR", message="The request contains invalid data", details=details),
    )


async def http_error_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    code = HTTPStatus(exc.status_code).name
    return _error_response(exc.status_code, ErrorBody(code=code, message=str(exc.detail)))


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, domain_error_handler)
    app.add_exception_handler(RequestValidationError, request_validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_error_handler)
