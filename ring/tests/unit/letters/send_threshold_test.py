"""Unit tests for letter send-threshold helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from ring.letters.constants import LetterStatus
from ring.letters.send_threshold import (
    DEFAULT_MIN_RESPONDER_RATIO_TO_SEND,
    GROUP_SETTING_MIN_RESPONDER_RATIO_KEY,
    GROUP_SETTING_MIN_RESPONDERS_KEY,
    effective_send_threshold_ratio,
    get_group_min_responder_ratio,
    is_below_send_threshold,
    letter_responder_count,
    minimum_responders_required,
    parse_positive_int,
    parse_ratio,
    set_group_min_responder_ratio,
)
from ring.parties.crud import group as group_crud
from ring.ring_pydantic.linked_schemas import MinimalLetter, PublicLetter
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.letters.question_factory import QuestionFactory
from ring.tests.factories.letters.response_factory import ResponseFactory
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory


class TestParseHelpers:
    """Tests for key-value parsing helpers."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (3, 3),
            ("4", 4),
            (4.0, 4),
            (0, None),
            (-1, None),
            (True, None),
            ("not-a-number", None),
            (2.5, None),
        ],
    )
    def test_parse_positive_int(
        self, value: object, expected: int | None
    ) -> None:
        assert parse_positive_int(value) == expected

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (0.0, 0.0),
            (0, 0.0),
            ("0", 0.0),
            (0.75, 0.75),
            ("0.5", 0.5),
            (1.0, 1.0),
            (-0.1, None),
            (1.1, None),
            (True, None),
            ("bad", None),
        ],
    )
    def test_parse_ratio(self, value: object, expected: float | None) -> None:
        assert parse_ratio(value) == expected


class TestSendThresholdPolicy:
    """Tests for group and letter threshold resolution."""

    def test_get_group_min_responder_ratio_unset(
        self, db_session: Session
    ) -> None:
        group = GroupFactory.create()
        db_session.commit()
        assert get_group_min_responder_ratio(group) is None

    def test_get_group_min_responder_ratio_configured(
        self, db_session: Session
    ) -> None:
        group = GroupFactory.create()
        group.key_values.set_value(GROUP_SETTING_MIN_RESPONDER_RATIO_KEY, 0.75)
        db_session.commit()
        assert get_group_min_responder_ratio(group) == 0.75

    def test_effective_ratio_uses_default_when_unset(
        self, db_session: Session
    ) -> None:
        group = GroupFactory.create()
        db_session.commit()
        assert effective_send_threshold_ratio(group) == (
            DEFAULT_MIN_RESPONDER_RATIO_TO_SEND
        )

    def test_effective_ratio_none_when_disabled(
        self, db_session: Session
    ) -> None:
        group = GroupFactory.create()
        group.key_values.set_value(GROUP_SETTING_MIN_RESPONDER_RATIO_KEY, 0)
        db_session.commit()
        assert effective_send_threshold_ratio(group) is None

    def test_effective_ratio_none_when_absolute_count_set(
        self, db_session: Session
    ) -> None:
        group = GroupFactory.create()
        group.key_values.set_value(GROUP_SETTING_MIN_RESPONDERS_KEY, 2)
        db_session.commit()
        assert effective_send_threshold_ratio(group) is None

    def test_minimum_responders_default_ratio(
        self, db_session: Session
    ) -> None:
        admin = UserFactory.create()
        members = [admin] + [UserFactory.create() for _ in range(3)]
        group = GroupFactory.create(admin=admin, members=members)
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            send_at=datetime.now(tz=UTC) + timedelta(days=1),
        )
        db_session.commit()
        assert minimum_responders_required(letter) == 2

    def test_minimum_responders_configured_ratio(
        self, db_session: Session
    ) -> None:
        admin = UserFactory.create()
        members = [admin] + [UserFactory.create() for _ in range(3)]
        group = GroupFactory.create(admin=admin, members=members)
        group.key_values.set_value(GROUP_SETTING_MIN_RESPONDER_RATIO_KEY, 0.75)
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            send_at=datetime.now(tz=UTC) + timedelta(days=1),
        )
        db_session.commit()
        assert minimum_responders_required(letter) == 3

    def test_minimum_responders_disabled_at_zero(
        self, db_session: Session
    ) -> None:
        admin = UserFactory.create()
        members = [admin] + [UserFactory.create() for _ in range(3)]
        group = GroupFactory.create(admin=admin, members=members)
        group.key_values.set_value(GROUP_SETTING_MIN_RESPONDER_RATIO_KEY, 0)
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            send_at=datetime.now(tz=UTC) + timedelta(days=1),
        )
        db_session.commit()
        assert minimum_responders_required(letter) == 0

    def test_minimum_responders_absolute_count_takes_precedence(
        self, db_session: Session
    ) -> None:
        admin = UserFactory.create()
        members = [admin] + [UserFactory.create() for _ in range(3)]
        group = GroupFactory.create(admin=admin, members=members)
        group.key_values.set_value(GROUP_SETTING_MIN_RESPONDERS_KEY, 3)
        group.key_values.set_value(GROUP_SETTING_MIN_RESPONDER_RATIO_KEY, 0.5)
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            send_at=datetime.now(tz=UTC) + timedelta(days=1),
        )
        db_session.commit()
        assert minimum_responders_required(letter) == 3

    def test_set_group_min_responder_ratio_persists_and_clears(
        self, db_session: Session
    ) -> None:
        group = GroupFactory.create()
        db_session.commit()

        set_group_min_responder_ratio(group, 0.6)
        assert get_group_min_responder_ratio(group) == 0.6

        set_group_min_responder_ratio(group, None)
        assert get_group_min_responder_ratio(group) is None

    def test_set_group_min_responder_ratio_rejects_invalid(self) -> None:
        group = GroupFactory.build()
        with pytest.raises(ValueError, match="between 0 and 1"):
            set_group_min_responder_ratio(group, 1.5)


class TestLetterResponderCount:
    """Responder counting stays consistent with the participant roster."""

    def test_removed_member_response_does_not_count(
        self, db_session: Session
    ) -> None:
        """A responder removed from the group stops counting toward the
        threshold, so their early reply cannot trigger a premature send
        once the participant denominator shrinks."""
        admin = UserFactory.create()
        members = [admin] + [UserFactory.create() for _ in range(2)]
        group = GroupFactory.create(admin=admin, members=members)
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            send_at=datetime.now(tz=UTC) + timedelta(days=1),
        )
        question = QuestionFactory.create(letter=letter)
        leaver = members[2]
        ResponseFactory.create(question=question, participant=leaver)
        db_session.commit()

        # 3 participants at the default ratio require 2 responders.
        assert minimum_responders_required(letter) == 2
        assert letter_responder_count(letter) == 1
        assert is_below_send_threshold(letter) is True

        group_crud.remove_member(
            db_session, group.api_identifier, leaver.api_identifier
        )
        db_session.commit()

        # 2 remaining participants require 1 responder, and the leaver's
        # response no longer counts, so the letter stays below threshold.
        assert minimum_responders_required(letter) == 1
        assert letter_responder_count(letter) == 0
        assert is_below_send_threshold(letter) is True

        ResponseFactory.create(question=question, participant=members[1])
        db_session.commit()

        assert letter_responder_count(letter) == 1
        assert is_below_send_threshold(letter) is False


class TestLetterSchemaThresholdFields:
    """Threshold progress fields are populated via schema validators only."""

    def test_public_letter_model_validate_includes_threshold_fields(
        self, db_session: Session
    ) -> None:
        admin = UserFactory.create()
        members = [admin] + [UserFactory.create() for _ in range(3)]
        group = GroupFactory.create(admin=admin, members=members)
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            send_at=datetime.now(tz=UTC) + timedelta(days=1),
        )
        question = QuestionFactory.create(letter=letter)
        ResponseFactory.create(question=question, participant=members[0])
        db_session.commit()

        public_letter = PublicLetter.model_validate(letter)

        assert public_letter.required_responders == 2
        assert public_letter.responder_count == 1
        assert public_letter.send_threshold_ratio == (
            DEFAULT_MIN_RESPONDER_RATIO_TO_SEND
        )

    def test_public_letter_revalidate_preserves_threshold_fields(
        self, db_session: Session
    ) -> None:
        admin = UserFactory.create()
        members = [admin] + [UserFactory.create() for _ in range(3)]
        group = GroupFactory.create(admin=admin, members=members)
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            send_at=datetime.now(tz=UTC) + timedelta(days=1),
        )
        question = QuestionFactory.create(letter=letter)
        ResponseFactory.create(question=question, participant=members[0])
        db_session.commit()

        public_letter = PublicLetter.model_validate(letter)
        revalidated = PublicLetter.model_validate(public_letter)

        assert (
            revalidated.required_responders
            == public_letter.required_responders
        )
        assert revalidated.responder_count == public_letter.responder_count
        assert (
            revalidated.send_threshold_ratio
            == public_letter.send_threshold_ratio
        )

    def test_minimal_letter_model_validate_includes_threshold_fields(
        self, db_session: Session
    ) -> None:
        admin = UserFactory.create()
        members = [admin] + [UserFactory.create() for _ in range(3)]
        group = GroupFactory.create(admin=admin, members=members)
        group.key_values.set_value(GROUP_SETTING_MIN_RESPONDER_RATIO_KEY, 0)
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            send_at=datetime.now(tz=UTC) + timedelta(days=1),
        )
        question = QuestionFactory.create(letter=letter)
        ResponseFactory.create(question=question, participant=members[0])
        db_session.commit()

        minimal_letter = MinimalLetter.model_validate(letter)

        assert minimal_letter.required_responders == 0
        assert minimal_letter.responder_count == 1
        assert minimal_letter.send_threshold_ratio is None

    def test_letter_to_pydantic_uses_schema_validators_only(
        self, db_session: Session
    ) -> None:
        admin = UserFactory.create()
        group = GroupFactory.create(admin=admin, members=[admin])
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            send_at=datetime.now(tz=UTC) + timedelta(days=1),
        )
        db_session.commit()

        pydantic_letter = letter.to_pydantic()

        assert pydantic_letter.required_responders == 1
        assert pydantic_letter.responder_count == 0
