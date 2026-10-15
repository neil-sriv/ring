"""RFC 3339 helpers for ``created_at`` (instant compare, UTC ``Z``)."""

from __future__ import annotations

from datetime import UTC, datetime


def format_created_at(value: datetime | None) -> str:
    """UTC ``Z`` at second resolution, no fractional seconds."""
    instant = _as_utc(value if value is not None else datetime.now(UTC))
    return instant.strftime("%Y-%m-%dT%H:%M:%SZ")


def created_at_equal(
    left: datetime | str | None,
    right: datetime | str | None,
) -> bool:
    """Compare timestamps as instants, not strings."""
    if left is None or right is None:
        return left is None and right is None
    return _as_utc(left) == _as_utc(right)


def _as_utc(value: datetime | str) -> datetime:
    if isinstance(value, str):
        text = value.strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        parsed = datetime.fromisoformat(text)
    else:
        parsed = value
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC).replace(microsecond=0)
