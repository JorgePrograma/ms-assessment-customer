from datetime import UTC, datetime


def as_utc(value: datetime) -> datetime:
    """Returns `value` in UTC. Naive datetimes are assumed to already be UTC
    (timestamps are stored in UTC, but some backends such as SQLite drop the tzinfo on read)."""
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
