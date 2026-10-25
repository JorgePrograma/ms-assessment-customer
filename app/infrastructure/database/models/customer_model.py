from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities import CustomerStatus
from app.infrastructure.database.database import Base


class CustomerModel(Base):
    """Persistence model (SQLAlchemy ORM). Maps the `customers` table."""

    __tablename__ = "customers"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    status: Mapped[CustomerStatus] = mapped_column(
        Enum(CustomerStatus, name="customer_status", native_enum=False, create_constraint=True, length=20),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
