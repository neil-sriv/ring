"""Tests for the group CRUD operations.

This module contains tests for all group-related database operations,
including group creation, member management, and group settings.
It verifies both successful operations and error cases.
"""

from __future__ import annotations

import pytest
import sqlalchemy
from faker import Faker
from sqlalchemy.orm import Session

from ring.letters.constants import DEFAULT_QUESTIONS, LetterStatus
from ring.parties.crud import group as group_crud
from ring.parties.models.group_model import Group
from ring.parties.models.user_model import User
from ring.tasks.models.task_model import Task, TaskType
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory


class TestGroupCrud:
    """Test suite for group CRUD operations.

    This class contains tests for all group-related database operations,
    including CRUD operations, member management, and group settings.
    """

    def test_get_groups(self, db_session: Session) -> None:
        """Test retrieving groups for a user.

        This test verifies that:
        1. Groups where the user is admin are included
        2. Groups where the user is a member are included
        3. Other groups are not included
        4. The returned list contains all relevant groups

        Args:
            db_session (Session): Database session
        """
        [GroupFactory.create() for _ in range(5)]
        user = UserFactory.create()
        db_session.commit()

        assert group_crud.get_groups(db_session, user.api_identifier) == []

        user_admin_groups = [GroupFactory.create(admin=user) for _ in range(5)]
        user_member_groups = [GroupFactory.create() for _ in range(5)]
        for group in user_member_groups:
            group.members.append(user)
        db_session.commit()

        groups = group_crud.get_groups(db_session, user.api_identifier)
        assert len(groups) == 10
        assert groups == user_admin_groups + user_member_groups

    def test_create_group(self, db_session: Session, faker: Faker) -> None:
        """Test creating a new group.

        This test verifies that:
        1. A group can be created with a valid name and admin
        2. The group has the correct name and admin
        3. The admin is added as a member
        4. Default questions are created
        5. The group is properly stored in the database

        Args:
            db_session (Session): Database session
            faker (Faker): Faker instance for generating test data
        """
        name = faker.name()
        admin = UserFactory.create()
        group = group_crud.create_group(db_session, admin.api_identifier, name)
        db_session.commit()

        assert group.name == name
        assert group.admin is admin
        assert group.members == [admin]
        assert group.created_at is not None

        assert [
            dq.question_text in DEFAULT_QUESTIONS
            for dq in group.default_questions
        ]

        db_group = db_session.scalars(
            sqlalchemy.select(Group).filter(
                Group.api_identifier == group.api_identifier
            )
        ).one()
        assert db_group == group

    def test_add_member(self, db_session: Session) -> None:
        """Test adding a member to a group.

        This test verifies that:
        1. A user can be added as a member
        2. The user is added to active letters
        3. The user is added to upcoming letters
        4. The group is returned

        Args:
            db_session (Session): Database session
        """
        group = GroupFactory.create()
        in_progress_letter = LetterFactory.create(
            group=group, status=LetterStatus.IN_PROGRESS
        )
        upcoming_letter = LetterFactory.create(
            group=group, status=LetterStatus.UPCOMING
        )
        user = UserFactory.create()
        db_session.commit()

        assert user not in group.members
        assert user not in in_progress_letter.participants
        assert user not in upcoming_letter.participants

        assert (
            group_crud.add_member(
                db_session, group.api_identifier, user.api_identifier
            )
            == group
        )

        assert user in group.members
        assert user in in_progress_letter.participants
        assert user in upcoming_letter.participants

    def test_remove_member(self, db_session: Session) -> None:
        """Test removing a member from a group.

        This test verifies that:
        1. A member can be removed from the group
        2. The group is returned
        3. The member is actually removed

        Args:
            db_session (Session): Database session
        """
        group = GroupFactory.create()
        user = UserFactory.create()
        group.members.append(user)
        db_session.commit()

        assert user in group.members

        assert (
            group_crud.remove_member(
                db_session, group.api_identifier, user.api_identifier
            )
            == group
        )

        assert user not in group.members

    def test_remove_member_duplicate(self, db_session: Session) -> None:
        """Test removing a member who is not in the group.

        This test verifies that:
        1. Removing a non-member raises an error
        2. The error message is correct
        3. The group state remains unchanged

        Args:
            db_session (Session): Database session
        """
        group = GroupFactory.create()
        user = UserFactory.create()
        group.members.append(user)
        db_session.commit()

        assert user in group.members

        group_crud.remove_member(
            db_session, group.api_identifier, user.api_identifier
        )
        db_session.commit()

        with pytest.raises(ValueError, match="is not a member of group"):
            group_crud.remove_member(
                db_session, group.api_identifier, user.api_identifier
            )

        assert user not in group.members

    def test_get_letter_by_api_id(self, db_session: Session) -> None:
        """Test retrieving a letter by its API identifier.

        This test verifies that:
        1. A letter can be retrieved by its API identifier
        2. The correct letter is returned
        3. An error is raised for invalid identifiers

        Args:
            db_session (Session): Database session
        """
        group = GroupFactory.create()
        letters = [
            LetterFactory.create(group=group, status=LetterStatus.IN_PROGRESS),
            LetterFactory.create(group=group, status=LetterStatus.UPCOMING),
        ]
        db_session.commit()

        assert (
            group_crud.get_letter_by_api_id(group, letters[0].api_identifier)
            == letters[0]
        )
        assert (
            group_crud.get_letter_by_api_id(group, letters[1].api_identifier)
            == letters[1]
        )
        with pytest.raises(
            ValueError, match="Could not find letter with api_id"
        ):
            group_crud.get_letter_by_api_id(group, "invalid")

    def test_add_members(self, db_session: Session) -> None:
        """Test adding multiple members to a group.

        This test verifies that:
        1. Multiple users can be added as members
        2. Existing members are not duplicated
        3. All users are added to the group

        Args:
            db_session (Session): Database session
        """
        group = GroupFactory.create()
        members = [UserFactory.create() for _ in range(5)]
        for member in members:
            group.members.append(member)
        users = [UserFactory.create() for _ in range(5)]
        db_session.commit()

        assert all(user not in group.members for user in users)

        group_crud.add_members(db_session, group, users + members)
        db_session.commit()

        assert all(user in group.members for user in users + members)

    def test_update_cycle_length(self, db_session: Session) -> None:
        """Test updating a group's cycle length.

        This test verifies that:
        1. The cycle length can be updated
        2. The group is returned
        3. The new cycle length is set correctly

        Args:
            db_session (Session): Database session
        """
        group = GroupFactory.create()
        db_session.commit()

        # Test updating to a valid cycle length
        updated_group = group_crud.update_cycle_length(db_session, group, 60)
        db_session.commit()

        assert updated_group == group
        assert updated_group.cycle_length == 60

    def test_get_cycle_length(self, db_session: Session) -> None:
        """Test retrieving a group's cycle length.

        This test verifies that:
        1. The correct cycle length is returned
        2. The value matches what was set

        Args:
            db_session (Session): Database session
        """
        group = GroupFactory.create()
        group.cycle_length = 45
        db_session.commit()

        cycle_length = group_crud.get_cycle_length(db_session, group)
        assert cycle_length == 45
