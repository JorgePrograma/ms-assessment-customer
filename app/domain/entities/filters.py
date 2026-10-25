from dataclasses import dataclass

from app.domain.entities.customer import CustomerStatus


@dataclass(frozen=True, slots=True)
class CustomerFilters:
    status: CustomerStatus | None = None
    search: str | None = None
