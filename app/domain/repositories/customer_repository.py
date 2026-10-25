from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from datetime import datetime
from uuid import UUID

from app.domain.entities import Customer, CustomerFilters, CustomerStatus
from app.shared.pagination import Page, PageRequest


class CustomerRepository(ABC):
    """Port: persistence contract the use cases depend on (Dependency Inversion).

    The implementation lives in `infrastructure/repositories`; the domain never imports it.
    """

    @abstractmethod
    def add(self, customer: Customer) -> Customer: ...

    @abstractmethod
    def get_by_id(self, customer_id: UUID) -> Customer | None: ...

    @abstractmethod
    def get_by_email(self, email: str) -> Customer | None: ...

    @abstractmethod
    def list(self, page_request: PageRequest, filters: CustomerFilters) -> Page[Customer]: ...

    @abstractmethod
    def update(self, customer: Customer) -> Customer: ...

    @abstractmethod
    def count_by_status(self) -> Mapping[CustomerStatus, int]:
        """Number of customers per status; statuses without customers may be omitted."""

    @abstractmethod
    def created_since(self, since: datetime) -> Sequence[datetime]:
        """Registration timestamps from `since` (inclusive) onwards."""
