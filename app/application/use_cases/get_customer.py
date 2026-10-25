from uuid import UUID

from app.domain.entities import Customer
from app.domain.errors import CustomerNotFoundError
from app.domain.repositories import CustomerRepository


class GetCustomerUseCase:
    def __init__(self, repository: CustomerRepository) -> None:
        self._repository = repository

    def execute(self, customer_id: UUID) -> Customer:
        customer = self._repository.get_by_id(customer_id)
        if customer is None:
            raise CustomerNotFoundError(customer_id)
        return customer
