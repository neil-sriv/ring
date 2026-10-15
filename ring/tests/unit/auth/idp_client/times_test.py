"""RFC 3339 created_at instant compare."""

from __future__ import annotations

from datetime import UTC, datetime

from ring.auth.idp_client.times import created_at_equal, format_created_at


def test_format_and_compare_instants() -> None:
    value = datetime(2024, 1, 15, 12, 0, 0, 123456, tzinfo=UTC)
    assert format_created_at(value) == "2024-01-15T12:00:00Z"
    assert created_at_equal(value, "2024-01-15T12:00:00Z")
    assert created_at_equal(
        "2024-01-15T12:00:00+00:00", "2024-01-15T12:00:00Z"
    )
    assert not created_at_equal("2024-01-15T12:00:00Z", "2024-01-15T12:00:01Z")
