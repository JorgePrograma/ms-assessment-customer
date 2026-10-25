from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.domain.entities import CustomerFilters, CustomerStatus
from app.presentation.dependencies import (
    CreateCustomerDep,
    GetCustomerDep,
    GetCustomersSummaryDep,
    ListCustomersDep,
    UpdateCustomerStatusDep,
)
from app.presentation.dtos import (
    CreateCustomerRequest,
    CustomerResponse,
    CustomerSummaryResponse,
    UpdateCustomerStatusRequest,
)
from app.presentation.mappers import CustomerResponseMapper
from app.shared.api_response import ErrorResponse, PaginatedResponse, SuccessResponse, to_paginated_response
from app.shared.pagination import PageRequest

router = APIRouter(
    prefix="/customers",
    tags=["customers"],
    responses={status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse, "description": "Invalid request"}},
)

_NOT_FOUND = {status.HTTP_404_NOT_FOUND: {"model": ErrorResponse, "description": "Customer not found"}}


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_409_CONFLICT: {"model": ErrorResponse, "description": "Email already registered"}},
)
def create_customer(payload: CreateCustomerRequest, use_case: CreateCustomerDep) -> SuccessResponse[CustomerResponse]:
    customer = use_case.execute(name=payload.name, email=payload.email)
    return SuccessResponse(data=CustomerResponseMapper.to_response(customer))


@router.get("")
def list_customers(
    use_case: ListCustomersDep,
    status: CustomerStatus | None = None,
    search: Annotated[str | None, Query(max_length=100, description="Matches name or email (case-insensitive)")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginatedResponse[CustomerResponse]:
    filters = CustomerFilters(status=status, search=(search or "").strip() or None)
    result = use_case.execute(PageRequest(page=page, size=size), filters)
    return to_paginated_response(result, CustomerResponseMapper.to_response)


@router.get("/summary")
def get_customers_summary(
    use_case: GetCustomersSummaryDep,
    days: Annotated[int, Query(ge=7, le=90, description="Days of daily registrations to return")] = 14,
) -> SuccessResponse[CustomerSummaryResponse]:
    return SuccessResponse(data=CustomerResponseMapper.to_summary_response(use_case.execute(days=days)))


@router.get("/{customer_id}", responses=_NOT_FOUND)
def get_customer(customer_id: UUID, use_case: GetCustomerDep) -> SuccessResponse[CustomerResponse]:
    return SuccessResponse(data=CustomerResponseMapper.to_response(use_case.execute(customer_id)))


@router.patch("/{customer_id}/status", responses=_NOT_FOUND)
def update_customer_status(
    customer_id: UUID, payload: UpdateCustomerStatusRequest, use_case: UpdateCustomerStatusDep
) -> SuccessResponse[CustomerResponse]:
    customer = use_case.execute(customer_id, payload.status)
    return SuccessResponse(data=CustomerResponseMapper.to_response(customer))
