from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


class CustomerStatus(StrEnum):
    ACTIVE = "ACTIVE"
    PENDING = "PENDING"
    BLOCKED = "BLOCKED"


@dataclass(slots=True)
class Customer:
    name: str
    email: str
    status: CustomerStatus = CustomerStatus.PENDING
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def register(cls, name: str, email: str) -> Customer:
        return cls(name=name.strip(), email=email.strip().lower(), status=CustomerStatus.PENDING)

    def change_status(self, new_status: CustomerStatus) -> None:
        self.status = new_status
