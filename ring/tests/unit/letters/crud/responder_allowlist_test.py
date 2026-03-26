"""Tests for responder allowlist resolution and response validation."""

from __future__ import annotations

from datetime import UTC

import pytest
from faker import Faker
from sqlalchemy.orm import Session

from ring.letters.constants import LetterStatus
from ring.letters.crud import question as question_crud
from ring.letters.crud.responder_allowlist import (
    set_group_responder_allowlist,
    set_letter_responder_allowlist,
)
from ring.letters.models.letter_model import Letter
from ring.tests.factories.letters.question_factory import QuestionFactory
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory


def test_effective_responders_letter_overrides_group(
    db_session: Session, faker: Faker
) -> None:
    members = [UserFactory.create() for _ in range(3)]
    group = GroupFactory.create(admin=members[0])
    for m in members:
        group.members.append(m)
    db_session.commit()
    set_group_responder_allowlist(db_session, group, [members[0]])
    letter = Letter(
        group=group,
        send_at=faker.date_time(tzinfo=UTC),
        status=LetterStatus.IN_PROGRESS,
    )
    db_session.add(letter)
    db_session.commit()
    set_letter_responder_allowlist(db_session, letter, [members[1], members[2]])
    db_session.commit()
    assert set(letter.effective_responders) == {members[1], members[2]}


def test_effective_responders_falls_back_to_group(
    db_session: Session, faker: Faker
) -> None:
    members = [UserFactory.create() for _ in range(2)]
    group = GroupFactory.create(admin=members[0])
    for m in members:
        group.members.append(m)
    db_session.commit()
    set_group_responder_allowlist(db_session, group, [members[0]])
    letter = Letter(
        group=group,
        send_at=faker.date_time(tzinfo=UTC),
        status=LetterStatus.IN_PROGRESS,
    )
    db_session.add(letter)
    db_session.commit()
    assert letter.effective_responders == [members[0]]


def test_add_response_rejects_non_responder(
    db_session: Session, faker: Faker
) -> None:
    members = [UserFactory.create() for _ in range(2)]
    group = GroupFactory.create(admin=members[0])
    for m in members:
        group.members.append(m)
    db_session.commit()
    letter = Letter(
        group=group,
        send_at=faker.date_time(tzinfo=UTC),
        status=LetterStatus.IN_PROGRESS,
    )
    db_session.add(letter)
    db_session.commit()
    set_letter_responder_allowlist(db_session, letter, [members[0]])
    question = QuestionFactory.create(letter=letter)
    db_session.commit()

    question_crud.add_response(db_session, question, members[0], "ok")
    db_session.commit()

    with pytest.raises(ValueError, match="not allowed to respond"):
        question_crud.add_response(db_session, question, members[1], "no")
