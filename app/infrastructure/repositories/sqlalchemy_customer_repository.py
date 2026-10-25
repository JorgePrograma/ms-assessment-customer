from collections.abc import Mapping, Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import ColumnElement, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.entities import Customer, CustomerFilters, CustomerStatus
from app.domain.errors import CustomerNotFoundError, EmailAlreadyExistsError
from app.domain.repositories import CustomerRepository
from app.infrastructure.database.models import CustomerModel
from app.infrastructure.mappers import CustomerModelMapper
from app.shared.pagination import Page, PageRequest


def _build_conditions(filters: CustomerFilters) -> list[ColumnElement[bool]]:
    conditions: list[ColumnElement[bool]] = []
    if filters.status is not None:
        conditions.append(CustomerModel.status == filters.status)
    if filters.search:
        escaped = filters.search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{escaped}%"
        conditions.append(
            or_(CustomerModel.name.ilike(pattern, escape="\\"), CustomerModel.email.ilike(pattern, escape="\\"))
        )
    return conditions


class SqlAlchemyCustomerRepository(CustomerRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, customer: Customer) -> Customer:
        model = CustomerModelMapper.to_model(customer)
        self._session.add(model)
        try:
            self._session.commit()
        except IntegrityError as exc:
            self._session.rollback()
            raise EmailAlreadyExistsError(customer.email) from exc
        return CustomerModelMapper.to_entity(model)

    def get_by_id(self, customer_id: UUID) -> Customer | None:
        model = self._session.get(CustomerModel, customer_id)
        return CustomerModelMapper.to_entity(model) if model else None

    def get_by_email(self, email: str) -> Customer | None:
        model = self._session.scalar(select(CustomerModel).where(CustomerModel.email == email))
        return CustomerModelMapper.to_entity(model) if model else None

    def list(self, page_request: PageRequest, filters: CustomerFilters) -> Page[Customer]:
        conditions = _build_conditions(filters)

        total = self._session.scalar(select(func.count()).select_from(CustomerModel).where(*conditions)) or 0
        query = (
            select(CustomerModel)
            .where(*conditions)
            .order_by(CustomerModel.created_at.desc(), CustomerModel.id.desc())
            .offset(page_request.offset)
            .limit(page_request.size)
        )
        items = [CustomerModelMapper.to_entity(model) for model in self._session.scalars(query)]
        return Page(items=items, total=total, page=page_request.page, size=page_request.size)

    def count_by_status(self) -> Mapping[CustomerStatus, int]:
        rows = self._session.execute(select(CustomerModel.status, func.count()).group_by(CustomerModel.status)).all()
        return {status: count for status, count in rows}

    def created_since(self, since: datetime) -> Sequence[datetime]:
        query = select(CustomerModel.created_at).where(CustomerModel.created_at >= since)
        return list(self._session.scalars(query))

    def update(self, customer: Customer) -> Customer:
        model = self._session.get(CustomerModel, customer.id)
        if model is None:
            raise CustomerNotFoundError(customer.id)
        model.name = customer.name
        model.email = customer.email
        model.status = customer.status
        self._session.commit()
        return CustomerModelMapper.to_entity(model)
