from http import HTTPStatus
from uuid import UUID


class DomainError(Exception):
    code: str = "DOMAIN_ERROR"
    status_code: int = HTTPStatus.BAD_REQUEST

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ValidationError(DomainError):
    code = "VALIDATION_ERROR"
    status_code = HTTPStatus.UNPROCESSABLE_CONTENT

    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.field = field


class CustomerNotFoundError(DomainError):
    code = "CUSTOMER_NOT_FOUND"
    status_code = HTTPStatus.NOT_FOUND

    def __init__(self, customer_id: UUID) -> None:
        super().__init__(f"Customer '{customer_id}' not found")


class EmailAlreadyExistsError(DomainError):
    code = "EMAIL_ALREADY_EXISTS"
    status_code = HTTPStatus.CONFLICT

    def __init__(self, email: str) -> None:
        super().__init__(f"A customer with email '{email}' already exists")
