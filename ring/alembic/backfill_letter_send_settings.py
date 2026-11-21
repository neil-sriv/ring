"""Copy letter-send settings from the group store onto group columns.

The Alembic revision calls these functions. Tests call the same functions
so the upgrade path is what gets exercised.

Parsers are copied here on purpose. A later change to the app helpers must
not change how this revision reads rows that already exist.
"""

from __future__ import annotations

import json
import math
from numbers import Real
from typing import Any

import sqlalchemy as sa
from sqlalchemy.engine import Connection

_MIN_RESPONDERS_KEY = "letter_send_min_responders"
_MIN_RESPONDER_RATIO_KEY = "letter_send_min_responder_ratio"
_SETTING_KEYS = (
    _MIN_RESPONDERS_KEY,
    _MIN_RESPONDER_RATIO_KEY,
)


def _parse_positive_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    if isinstance(value, float):
        if math.isfinite(value) and value.is_integer() and value > 0:
            return int(value)
        return None
    if isinstance(value, str):
        try:
            parsed = float(value)
        except ValueError:
            return None
        if math.isfinite(parsed) and parsed.is_integer() and parsed > 0:
            return int(parsed)
    return None


def _parse_ratio(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, str):
        try:
            value = float(value)
        except ValueError:
            return None
    elif not isinstance(value, Real):
        return None
    ratio = float(value)
    if not math.isfinite(ratio) or ratio < 0 or ratio > 1:
        return None
    return ratio


def _as_dict(raw: Any) -> dict[str, Any]:
    if isinstance(raw, str):
        loaded = json.loads(raw)
        if isinstance(loaded, dict):
            return dict(loaded)
        return {}
    if isinstance(raw, dict):
        return dict(raw)
    return {}


def _write_store(
    connection: Connection, row_id: int, values: dict[str, Any]
) -> None:
    connection.execute(
        sa.text(
            "UPDATE group_key_value "
            "SET key_values = CAST(:key_values AS JSONB) "
            "WHERE id = :id"
        ),
        {"key_values": json.dumps(values), "id": row_id},
    )


def copy_letter_send_settings(connection: Connection) -> None:
    """Copy parsable letter-send keys onto the group and remove them."""
    rows = connection.execute(
        sa.text("SELECT id, group_id, key_values FROM group_key_value")
    ).mappings()
    for row in rows:
        values = _as_dict(row["key_values"])
        if not any(key in values for key in _SETTING_KEYS):
            continue
        responders = _parse_positive_int(values.pop(_MIN_RESPONDERS_KEY, None))
        ratio = _parse_ratio(values.pop(_MIN_RESPONDER_RATIO_KEY, None))
        connection.execute(
            sa.text(
                'UPDATE "group" SET min_responders = :responders, '
                "min_responder_ratio = :ratio WHERE id = :group_id"
            ),
            {
                "responders": responders,
                "ratio": ratio,
                "group_id": row["group_id"],
            },
        )
        _write_store(connection, row["id"], values)


def restore_letter_send_settings(connection: Connection) -> None:
    """Put column values back into the store before the columns are dropped."""
    rows = connection.execute(
        sa.text(
            "SELECT id, min_responders, min_responder_ratio FROM " '"group"'
        )
    ).mappings()
    for row in rows:
        if (
            row["min_responders"] is None
            and row["min_responder_ratio"] is None
        ):
            continue
        stored = (
            connection.execute(
                sa.text(
                    "SELECT id, key_values FROM group_key_value "
                    "WHERE group_id = :group_id"
                ),
                {"group_id": row["id"]},
            )
            .mappings()
            .first()
        )
        if stored is None:
            continue
        values = _as_dict(stored["key_values"])
        if row["min_responders"] is not None:
            values[_MIN_RESPONDERS_KEY] = int(row["min_responders"])
        if row["min_responder_ratio"] is not None:
            values[_MIN_RESPONDER_RATIO_KEY] = float(
                row["min_responder_ratio"]
            )
        _write_store(connection, stored["id"], values)
