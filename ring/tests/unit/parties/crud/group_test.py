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
    def test_get_groups(self, db_session: Session) -> None:
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

    def test_schedule_send(self, db_session: Session) -> None:
        group = GroupFactory.create()
        letter = LetterFactory.create(group=group)
        db_session.execute(sqlalchemy.delete(Task))
        db_session.commit()

        group_crud.schedule_send(
            db_session,
            group.api_identifier,
            letter.api_identifier,
            letter.send_at,
        )
        db_session.commit()

        assert len(group.schedule.tasks) == 1
        [task] = group.schedule.tasks
        assert task.type == TaskType.SEND_EMAIL
        assert group.schedule.send_email_tasks == [task]
        assert task.execute_at == letter.send_at
        assert task.arguments == {"letter_api_id": letter.api_identifier}

    def test_add_members(self, db_session: Session) -> None:
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
