"""Translates between the persistence model (SQLAlchemy) and the domain entity."""

from app.domain.entities import Customer
from app.infrastructure.database.models import CustomerModel
from app.shared.utils import as_utc


class CustomerModelMapper:
    @staticmethod
    def to_entity(model: CustomerModel) -> Customer:
        return Customer(
            id=model.id,
            name=model.name,
            email=model.email,
            status=model.status,
            created_at=as_utc(model.created_at),
        )

    @staticmethod
    def to_model(entity: Customer) -> CustomerModel:
        return CustomerModel(
            id=entity.id,
            name=entity.name,
            email=entity.email,
            status=entity.status,
            created_at=entity.created_at,
        )
