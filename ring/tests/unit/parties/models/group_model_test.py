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
    def test_group_model(self, db_session: Session, faker: Faker):
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

        db_group = db_session.scalars(
            sqlalchemy.select(Group).filter(Group.name == name)
        ).one()
        assert db_group == group

    def test_group_model_letters(self, db_session: Session, faker: Faker):
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
        assert group.in_progress_letter in letters
        assert group.upcoming_letter in letters

    def test_group_model_schedule(self, db_session: Session, faker: Faker):
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
