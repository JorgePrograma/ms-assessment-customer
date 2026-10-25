"""Standard response envelope shared by every endpoint (see specs/customers.spec.md §3)."""

from collections.abc import Callable
from typing import Literal

from pydantic import BaseModel

from app.shared.pagination import Page


class PaginationMeta(BaseModel):
    page: int
    size: int
    total: int
    pages: int


class SuccessResponse[T](BaseModel):
    success: Literal[True] = True
    data: T


class PaginatedResponse[T](BaseModel):
    success: Literal[True] = True
    data: list[T]
    meta: PaginationMeta


class ErrorDetail(BaseModel):
    field: str | None = None
    message: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail] | None = None


class ErrorResponse(BaseModel):
    success: Literal[False] = False
    error: ErrorBody


def to_paginated_response[T, R](page: Page[T], map_item: Callable[[T], R]) -> PaginatedResponse[R]:
    return PaginatedResponse[R](
        data=[map_item(item) for item in page.items],
        meta=PaginationMeta(page=page.page, size=page.size, total=page.total, pages=page.pages),
    )
