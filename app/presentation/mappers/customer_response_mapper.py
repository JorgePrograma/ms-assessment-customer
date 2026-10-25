from app.domain.entities import Customer, CustomerSummary
from app.presentation.dtos import CustomerResponse, CustomerSummaryResponse, DailyRegistrationsResponse


class CustomerResponseMapper:
    @staticmethod
    def to_response(entity: Customer) -> CustomerResponse:
        return CustomerResponse(
            id=entity.id,
            name=entity.name,
            email=entity.email,
            status=entity.status,
            created_at=entity.created_at,
        )

    @staticmethod
    def to_summary_response(summary: CustomerSummary) -> CustomerSummaryResponse:
        return CustomerSummaryResponse(
            total=summary.total,
            by_status=summary.by_status,
            registrations=[
                DailyRegistrationsResponse(date=item.day, count=item.count) for item in summary.registrations
            ],
        )
