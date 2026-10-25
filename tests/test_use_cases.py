"""Unit tests for the application layer: use cases run against an in-memory repository (no DB, no HTTP)."""

from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime
from uuid import UUID, uuid4

import pytest

from app.application.use_cases import (
    CreateCustomerUseCase,
    GetCustomersSummaryUseCase,
    GetCustomerUseCase,
    ListCustomersUseCase,
    UpdateCustomerStatusUseCase,
)
from app.domain.entities import Customer, CustomerFilters, CustomerStatus
from app.domain.errors import CustomerNotFoundError, EmailAlreadyExistsError, ValidationError
from app.domain.repositories import CustomerRepository
from app.shared.pagination import Page, PageRequest


class InMemoryCustomerRepository(CustomerRepository):
    def __init__(self) -> None:
        self._customers: dict[UUID, Customer] = {}

    def add(self, customer: Customer) -> Customer:
        self._customers[customer.id] = customer
        return customer

    def get_by_id(self, customer_id: UUID) -> Customer | None:
        return self._customers.get(customer_id)

    def get_by_email(self, email: str) -> Customer | None:
        return next((c for c in self._customers.values() if c.email == email), None)

    def list(self, page_request: PageRequest, filters: CustomerFilters) -> Page[Customer]:
        matches = [c for c in self._customers.values() if filters.status is None or c.status == filters.status]
        items = matches[page_request.offset : page_request.offset + page_request.size]
        return Page(items=items, total=len(matches), page=page_request.page, size=page_request.size)

    def update(self, customer: Customer) -> Customer:
        self._customers[customer.id] = customer
        return customer

    def count_by_status(self) -> Mapping[CustomerStatus, int]:
        return Counter(c.status for c in self._customers.values())

    def created_since(self, since: datetime) -> Sequence[datetime]:
        return [c.created_at for c in self._customers.values() if c.created_at >= since]


@pytest.fixture
def repository() -> InMemoryCustomerRepository:
    return InMemoryCustomerRepository()


@pytest.fixture
def create(repository: InMemoryCustomerRepository) -> CreateCustomerUseCase:
    return CreateCustomerUseCase(repository)


def test_new_customer_starts_as_pending_with_normalized_email(create: CreateCustomerUseCase) -> None:
    customer = create.execute(name="  Juan Pérez ", email="Juan@Example.com")

    assert customer.status is CustomerStatus.PENDING
    assert customer.name == "Juan Pérez"
    assert customer.email == "juan@example.com"


def test_duplicated_email_is_rejected_case_insensitively(create: CreateCustomerUseCase) -> None:
    create.execute(name="Juan", email="juan@example.com")

    with pytest.raises(EmailAlreadyExistsError):
        create.execute(name="Juan 2", email="JUAN@example.com")


@pytest.mark.parametrize(
    ("name", "email", "field"),
    [("   ", "juan@example.com", "name"), ("J" * 121, "juan@example.com", "name"), ("Juan", "juan@", "email")],
)
def test_domain_validator_protects_every_entry_point(
    create: CreateCustomerUseCase, name: str, email: str, field: str
) -> None:
    with pytest.raises(ValidationError) as error:
        create.execute(name=name, email=email)

    assert error.value.field == field


def test_get_unknown_customer_raises_not_found(repository: InMemoryCustomerRepository) -> None:
    with pytest.raises(CustomerNotFoundError):
        GetCustomerUseCase(repository).execute(uuid4())


def test_update_status_changes_customer_status(
    repository: InMemoryCustomerRepository, create: CreateCustomerUseCase
) -> None:
    customer = create.execute(name="Juan", email="juan@example.com")

    updated = UpdateCustomerStatusUseCase(repository).execute(customer.id, CustomerStatus.ACTIVE)

    assert updated.status is CustomerStatus.ACTIVE
    active = ListCustomersUseCase(repository).execute(PageRequest(), CustomerFilters(status=CustomerStatus.ACTIVE))
    assert active.items == [updated]


def test_update_status_of_unknown_customer_raises_not_found(repository: InMemoryCustomerRepository) -> None:
    with pytest.raises(CustomerNotFoundError):
        UpdateCustomerStatusUseCase(repository).execute(uuid4(), CustomerStatus.ACTIVE)


def test_summary_counts_every_status_and_zero_fills_registration_days(
    repository: InMemoryCustomerRepository,
) -> None:  # AC-25, AC-26
    now = datetime(2026, 10, 25, 15, 0, tzinfo=UTC)
    for name, created_at, status in [
        ("Old", datetime(2026, 9, 1, tzinfo=UTC), CustomerStatus.ACTIVE),
        ("First day", datetime(2026, 10, 19, 0, 0, tzinfo=UTC), CustomerStatus.PENDING),
        ("Today A", datetime(2026, 10, 25, 1, 0, tzinfo=UTC), CustomerStatus.PENDING),
        ("Today B", datetime(2026, 10, 25, 23, 59, tzinfo=UTC), CustomerStatus.ACTIVE),
    ]:
        repository.add(Customer(name=name, email=f"{name}@example.com", status=status, created_at=created_at))

    summary = GetCustomersSummaryUseCase(repository).execute(days=7, now=now)

    assert summary.total == 4
    assert summary.by_status == {CustomerStatus.ACTIVE: 2, CustomerStatus.PENDING: 2, CustomerStatus.BLOCKED: 0}
    assert [item.day for item in summary.registrations] == [date(2026, 10, day) for day in range(19, 26)]
    assert [item.count for item in summary.registrations] == [1, 0, 0, 0, 0, 0, 2]
