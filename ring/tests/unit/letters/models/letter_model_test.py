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
    def test_letter_model(self, db_session: Session, faker: Faker) -> None:
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
