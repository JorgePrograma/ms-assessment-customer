from dataclasses import dataclass

from app.domain.entities.customer import CustomerStatus


@dataclass(frozen=True, slots=True)
class CustomerFilters:
    """Criteria to narrow down a customer listing. Every field is optional and they combine with AND."""

    status: CustomerStatus | None = None
    search: str | None = None
