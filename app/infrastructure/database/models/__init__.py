"""ORM models. Importing this package registers every table in `Base.metadata` (used by Alembic)."""

from app.infrastructure.database.models.customer_model import CustomerModel

__all__ = ["CustomerModel"]
