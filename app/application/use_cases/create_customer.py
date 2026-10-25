import logging

from app.domain.entities import Customer
from app.domain.errors import EmailAlreadyExistsError
from app.domain.repositories import CustomerRepository
from app.domain.validators import CustomerValidator

logger = logging.getLogger(__name__)


class CreateCustomerUseCase:
    def __init__(self, repository: CustomerRepository) -> None:
        self._repository = repository

    def execute(self, name: str, email: str) -> Customer:
        CustomerValidator.validate_new(name, email)
        customer = Customer.register(name=name, email=email)
        if self._repository.get_by_email(customer.email) is not None:
            raise EmailAlreadyExistsError(customer.email)

        created = self._repository.add(customer)
        logger.info("Customer created id=%s status=%s", created.id, created.status)
        return created
