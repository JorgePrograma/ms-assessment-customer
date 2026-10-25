from collections import Counter
from datetime import UTC, datetime, time, timedelta

from app.domain.entities import CustomerStatus, CustomerSummary, DailyRegistrations
from app.domain.repositories import CustomerRepository
from app.shared.utils import as_utc


class GetCustomersSummaryUseCase:
    def __init__(self, repository: CustomerRepository) -> None:
        self._repository = repository

    def execute(self, days: int = 14, now: datetime | None = None) -> CustomerSummary:
        """Totals per status plus daily registrations (UTC days) for the last `days` days, zero-filled."""
        today = (now or datetime.now(UTC)).astimezone(UTC).date()
        first_day = today - timedelta(days=days - 1)

        counts = self._repository.count_by_status()
        by_status = {status: counts.get(status, 0) for status in CustomerStatus}

        since = datetime.combine(first_day, time.min, tzinfo=UTC)
        per_day = Counter(as_utc(created_at).date() for created_at in self._repository.created_since(since))
        registrations = [
            DailyRegistrations(day=day, count=per_day.get(day, 0))
            for day in (first_day + timedelta(days=offset) for offset in range(days))
        ]
        return CustomerSummary(total=sum(by_status.values()), by_status=by_status, registrations=registrations)
