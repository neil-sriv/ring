"""Upgrade coverage for moving letter-send settings out of the store."""

from __future__ import annotations

from sqlalchemy.orm import Session

from ring.alembic.backfill_letter_send_settings import (
    copy_letter_send_settings,
    restore_letter_send_settings,
)
from ring.tests.factories.parties.group_factory import GroupFactory


def test_upgrade_preserves_letter_send_settings(db_session: Session) -> None:
    """Parsable store values land on the columns and leave the dict."""
    group = GroupFactory.create()
    group.key_values.set_value("letter_send_min_responders", "4")
    group.key_values.set_value("letter_send_min_responder_ratio", 0.75)
    group.key_values.set_value("theme", "dark")

    untouched = GroupFactory.create()
    untouched.key_values.set_value("note", "stay")

    invalid = GroupFactory.create()
    invalid.key_values.set_value("letter_send_min_responders", True)
    invalid.key_values.set_value("letter_send_min_responder_ratio", "nope")
    invalid.key_values.set_value("keep", 1)
    db_session.commit()

    copy_letter_send_settings(db_session.connection())
    db_session.expire_all()

    assert group.min_responders == 4
    assert group.min_responder_ratio == 0.75
    assert dict(group.key_values.key_values) == {"theme": "dark"}

    assert untouched.min_responders is None
    assert untouched.min_responder_ratio is None
    assert dict(untouched.key_values.key_values) == {"note": "stay"}

    assert invalid.min_responders is None
    assert invalid.min_responder_ratio is None
    assert dict(invalid.key_values.key_values) == {"keep": 1}


def test_upgrade_preserves_disabled_ratio(db_session: Session) -> None:
    group = GroupFactory.create()
    group.key_values.set_value("letter_send_min_responder_ratio", "0")
    group.key_values.set_value("letter_send_min_responders", 3.0)
    db_session.commit()

    copy_letter_send_settings(db_session.connection())
    db_session.expire_all()

    assert group.min_responder_ratio == 0.0
    assert group.min_responders == 3
    assert dict(group.key_values.key_values) == {}


def test_downgrade_restores_store_keys(db_session: Session) -> None:
    group = GroupFactory.create()
    group.min_responders = 2
    group.min_responder_ratio = 0.25
    group.key_values.set_value("theme", "dark")
    db_session.commit()

    restore_letter_send_settings(db_session.connection())
    db_session.expire_all()

    assert dict(group.key_values.key_values) == {
        "theme": "dark",
        "letter_send_min_responders": 2,
        "letter_send_min_responder_ratio": 0.25,
    }
    assert group.min_responders == 2
    assert group.min_responder_ratio == 0.25
