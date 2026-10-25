import logging
from uuid import UUID

from app.domain.entities import Customer, CustomerStatus
from app.domain.errors import CustomerNotFoundError
from app.domain.repositories import CustomerRepository

logger = logging.getLogger(__name__)


class UpdateCustomerStatusUseCase:
    def __init__(self, repository: CustomerRepository) -> None:
        self._repository = repository

    def execute(self, customer_id: UUID, new_status: CustomerStatus) -> Customer:
        customer = self._repository.get_by_id(customer_id)
        if customer is None:
            raise CustomerNotFoundError(customer_id)

        previous_status = customer.status
        customer.change_status(new_status)
        updated = self._repository.update(customer)
        logger.info("Customer status changed id=%s %s -> %s", updated.id, previous_status, updated.status)
        return updated
