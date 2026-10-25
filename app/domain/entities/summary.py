from dataclasses import dataclass
from datetime import date

from app.domain.entities.customer import CustomerStatus


@dataclass(frozen=True, slots=True)
class DailyRegistrations:
    day: date
    count: int


@dataclass(frozen=True, slots=True)
class CustomerSummary:
    total: int
    by_status: dict[CustomerStatus, int]
    registrations: list[DailyRegistrations]
