from app.domain.entities import Customer, CustomerFilters
from app.domain.repositories import CustomerRepository
from app.shared.pagination import Page, PageRequest


class ListCustomersUseCase:
    def __init__(self, repository: CustomerRepository) -> None:
        self._repository = repository

    def execute(self, page_request: PageRequest, filters: CustomerFilters | None = None) -> Page[Customer]:
        return self._repository.list(page_request, filters or CustomerFilters())
