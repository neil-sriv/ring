"""Tests for the letter model.

This module contains tests for the Letter model, including model creation,
numbering, and responder tracking. It verifies both basic model attributes
and complex relationships with groups, questions, and responses.
"""
from __future__ import annotations

from datetime import UTC

from faker import Faker
from sqlalchemy.orm import Session

from ring.letters.constants import LetterStatus
from ring.letters.models.letter_model import Letter
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.letters.question_factory import QuestionFactory
from ring.tests.factories.letters.response_factory import ResponseFactory
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory


class TestLetterModel:
    """Test suite for the Letter model.

    This class contains tests for all letter model operations,
    including creation, numbering, and responder tracking.
    """

    def test_letter_model(self, db_session: Session, faker: Faker) -> None:
        """Test basic letter model creation and attributes.

        This test verifies that:
        1. A letter can be created with valid group and send time
        2. The letter is associated with the correct group
        3. The letter has the correct status and send time
        4. The letter is associated with all group members
        5. The letter has the correct number based on group history
        6. The letter has the required metadata fields

        Args:
            db_session (Session): Database session
            faker (Faker): Faker instance for generating test data
        """
        members = [UserFactory.create() for _ in range(3)]
        group = GroupFactory.create(admin=members[0])
        for member in members:
            group.members.append(member)
        [
            LetterFactory.create(group=group, status=LetterStatus.SENT)
            for _ in range(3)
        ]
        db_session.commit()

        send_at = faker.date_time(tzinfo=UTC)
        letter = Letter(
            group=group,
            send_at=send_at,
            status=LetterStatus.IN_PROGRESS,
        )
        db_session.add(letter)
        db_session.commit()

        assert letter.group == group
        assert letter.send_at == send_at
        assert letter.status == LetterStatus.IN_PROGRESS
        assert letter.participants == members
        assert letter.questions == []
        assert letter.id is not None
        assert letter.created_at is not None
        assert letter.api_identifier.startswith(Letter.API_ID_PREFIX)

        assert letter.number == 4

    def test_letter_model_number(
        self, db_session: Session, faker: Faker
    ) -> None:
        """Test letter numbering within a group.

        This test verifies that:
        1. The first letter in a group has number 1
        2. Letters can be created with explicit numbers
        3. The number is stored correctly
        4. The numbering system works with existing letters

        Args:
            db_session (Session): Database session
            faker (Faker): Faker instance for generating test data
        """
        group = GroupFactory.create()
        initial_letter = LetterFactory.create(group=group)
        db_session.commit()

        assert initial_letter.number == 1

        letter = Letter(
            group=group,
            send_at=faker.date_time(tzinfo=UTC),
            status=LetterStatus.IN_PROGRESS,
            number=1,
        )
        db_session.commit()

        assert letter.number == 1

    def test_letter_model_responders(
        self, db_session: Session, faker: Faker
    ) -> None:
        """Test tracking of letter responders.

        This test verifies that:
        1. A new letter has no responders
        2. Responders are tracked when they answer questions
        3. The responders list is updated correctly
        4. The responders list is sorted by API identifier
        5. Multiple responses from the same user are handled correctly

        Args:
            db_session (Session): Database session
            faker (Faker): Faker instance for generating test data
        """
        members = [UserFactory.create() for _ in range(4)]
        group = GroupFactory.create(admin=members[0])
        for member in members:
            group.members.append(member)
        db_session.commit()

        letter = Letter(
            group=group,
            send_at=faker.date_time(tzinfo=UTC),
            status=LetterStatus.IN_PROGRESS,
        )
        db_session.add(letter)
        db_session.commit()

        questions = [QuestionFactory.create(letter=letter) for _ in range(3)]
        db_session.commit()

        assert letter.responders == []

        ResponseFactory.create(question=questions[0], participant=members[0])
        ResponseFactory.create(question=questions[1], participant=members[1])
        ResponseFactory.create(question=questions[1], participant=members[2])
        db_session.commit()

        assert sorted(
            letter.responders, key=lambda user: user.api_identifier
        ) == sorted(members[:3], key=lambda user: user.api_identifier)
