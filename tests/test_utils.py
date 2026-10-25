from datetime import UTC, datetime, timedelta, timezone

from app.shared.utils import as_utc


def test_naive_datetime_is_assumed_to_be_utc() -> None:
    assert as_utc(datetime(2026, 10, 25, 8, 30)) == datetime(2026, 10, 25, 8, 30, tzinfo=UTC)


def test_aware_datetime_is_converted_to_utc() -> None:
    bogota = timezone(timedelta(hours=-5))

    converted = as_utc(datetime(2026, 10, 25, 22, 0, tzinfo=bogota))

    assert converted == datetime(2026, 10, 26, 3, 0, tzinfo=UTC)
    assert converted.tzinfo is UTC
