from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.application.use_cases import (
    CreateCustomerUseCase,
    GetCustomersSummaryUseCase,
    GetCustomerUseCase,
    ListCustomersUseCase,
    UpdateCustomerStatusUseCase,
)
from app.domain.repositories import CustomerRepository
from app.infrastructure.database import get_db
from app.infrastructure.repositories import SqlAlchemyCustomerRepository


def get_customer_repository(session: Annotated[Session, Depends(get_db)]) -> CustomerRepository:
    return SqlAlchemyCustomerRepository(session)


_Repository = Annotated[CustomerRepository, Depends(get_customer_repository)]


def get_create_customer(repository: _Repository) -> CreateCustomerUseCase:
    return CreateCustomerUseCase(repository)


def get_list_customers(repository: _Repository) -> ListCustomersUseCase:
    return ListCustomersUseCase(repository)


def get_get_customer(repository: _Repository) -> GetCustomerUseCase:
    return GetCustomerUseCase(repository)


def get_update_customer_status(repository: _Repository) -> UpdateCustomerStatusUseCase:
    return UpdateCustomerStatusUseCase(repository)


def get_customers_summary(repository: _Repository) -> GetCustomersSummaryUseCase:
    return GetCustomersSummaryUseCase(repository)


CreateCustomerDep = Annotated[CreateCustomerUseCase, Depends(get_create_customer)]
ListCustomersDep = Annotated[ListCustomersUseCase, Depends(get_list_customers)]
GetCustomerDep = Annotated[GetCustomerUseCase, Depends(get_get_customer)]
UpdateCustomerStatusDep = Annotated[UpdateCustomerStatusUseCase, Depends(get_update_customer_status)]
GetCustomersSummaryDep = Annotated[GetCustomersSummaryUseCase, Depends(get_customers_summary)]
