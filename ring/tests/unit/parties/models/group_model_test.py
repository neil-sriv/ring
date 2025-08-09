"""Tests for the group model.

This module contains tests for the group model's functionality,
including model creation, relationships, and default values.
It verifies both model attributes and relationships with other models.
"""

from __future__ import annotations

import sqlalchemy
from faker import Faker
from sqlalchemy.orm import Session

from ring.letters.constants import LetterStatus
from ring.parties.models.group_model import Group
from ring.tests.factories.letters.default_question_factory import (
    DefaultQuestionFactory,
)
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.parties.user_factory import UserFactory


class TestGroupModel:
    """Test suite for the group model.

    This class contains tests for all group model functionality,
    including model creation, relationships, and default values.
    """

    def test_group_model(self, db_session: Session, faker: Faker):
        """Test basic group model creation and attributes.

        This test verifies that:
        1. A group can be created with a name and admin
        2. The group has the correct name and admin
        3. The admin is added as a member
        4. The group has the correct API identifier prefix
        5. The group has default values for cycle length
        6. The group is properly stored in the database

        Args:
            db_session (Session): Database session
            faker (Faker): Faker instance for generating test data
        """
        name = faker.pystr_format(string_format="Group-{{random_int}}")
        admin_user = UserFactory.create()
        group = Group.create(name=name, admin=admin_user)
        db_session.add(group)
        db_session.commit()

        assert group.name == name
        assert group.admin == admin_user
        assert group.members == [admin_user]
        assert group.api_identifier.startswith(Group.API_ID_PREFIX)
        assert group.id is not None
        assert group.created_at is not None
        assert group.cycle_length == 30  # Default value

        db_group = db_session.scalars(
            sqlalchemy.select(Group).filter(Group.name == name)
        ).one()
        assert db_group == group

    def test_group_model_letters(self, db_session: Session, faker: Faker):
        """Test group model's relationship with letters.

        This test verifies that:
        1. A new group has no letters
        2. Letters can be added to the group
        3. The group can access its letters
        4. The group can access in-progress and upcoming letters
        5. The letters are properly associated with the group

        Args:
            db_session (Session): Database session
            faker (Faker): Faker instance for generating test data
        """
        name = faker.pystr_format(string_format="Group-{{random_int}}")
        admin_user = UserFactory.create()
        group = Group.create(name=name, admin=admin_user)
        db_session.add(group)
        db_session.commit()

        assert group.letters == []

        letters = [
            LetterFactory.create(group=group, status=LetterStatus.IN_PROGRESS),
            LetterFactory.create(group=group, status=LetterStatus.UPCOMING),
        ]
        db_session.commit()

        assert group.letters == letters
        assert group.cyclic_letters == letters
        assert group.in_progress_letters == [letters[0]]
        assert group.upcoming_letters == [letters[1]]

    def test_group_model_schedule(self, db_session: Session, faker: Faker):
        """Test group model's relationship with schedule.

        This test verifies that:
        1. A group has a schedule
        2. The schedule is properly associated with the group
        3. The schedule has a valid ID

        Args:
            db_session (Session): Database session
            faker (Faker): Faker instance for generating test data
        """
        name = faker.pystr_format(string_format="Group-{{random_int}}")
        admin_user = UserFactory.create()
        group = Group.create(name=name, admin=admin_user)
        db_session.add(group)
        db_session.commit()

        assert group.schedule.group == group
        assert group.schedule.id is not None

    def test_group_model_default_questions(
        self, db_session: Session, faker: Faker
    ):
        """Test group model's relationship with default questions.

        This test verifies that:
        1. A new group has no default questions
        2. Default questions can be added to the group
        3. The group can access its default questions
        4. The questions are properly associated with the group

        Args:
            db_session (Session): Database session
            faker (Faker): Faker instance for generating test data
        """
        name = faker.pystr_format(string_format="Group-{{random_int}}")
        admin_user = UserFactory.create()
        group = Group.create(name=name, admin=admin_user)
        db_session.add(group)
        db_session.commit()

        assert group.default_questions == []

        default_questions = [
            DefaultQuestionFactory.create(group=group),
            DefaultQuestionFactory.create(group=group),
        ]
        db_session.commit()

        assert group.default_questions == default_questions
        assert group.default_questions[0].group == group
        assert group.default_questions[1].group == group
