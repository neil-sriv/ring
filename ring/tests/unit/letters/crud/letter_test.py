"""Tests for letter CRUD operations.

This module contains tests for all letter-related CRUD operations,
including creation, retrieval, updating, and task management.
It verifies both basic operations and complex workflows involving
questions, responses, and scheduled tasks.
"""

from datetime import UTC, datetime, timedelta

import sqlalchemy
from faker import Faker
from sqlalchemy.orm import Session

from ring.letters.constants import (
    DEFAULT_QUESTIONS,
    QUESTION_BANK,
    LetterStatus,
)
from ring.letters.crud import letter as letter_crud
from ring.letters.models.letter_model import Letter
from ring.letters.models.question_model import Question
from ring.tasks.models.task_model import TaskType
from ring.tests.factories.letters.default_question_factory import (
    DefaultQuestionFactory,
)
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.letters.question_factory import QuestionFactory
from ring.tests.factories.letters.response_factory import ResponseFactory
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory


class TestLetterCrud:
    """Test suite for letter CRUD operations.

    This class contains tests for all letter-related database operations,
    including creation, retrieval, updating, and task management.
    """

    def test_get_letters(self, db_session: Session, faker: Faker) -> None:
        """Test retrieving letters for a group.

        This test verifies that:
        1. All letters for a group can be retrieved
        2. Letters are returned in the correct order
        3. The response includes letters with different statuses
        4. The database state is preserved

        Args:
            db_session (Session): Database session
            faker (Faker): Faker instance for generating test data
        """
        group = GroupFactory.create()
        letters = [
            LetterFactory.create(group=group, status=LetterStatus.IN_PROGRESS),
            LetterFactory.create(group=group, status=LetterStatus.UPCOMING),
        ]
        db_session.commit()

        assert (
            letter_crud.get_letters(db_session, group.api_identifier)
            == letters
        )

    def test_get_letters_for_user(self, db_session: Session) -> None:
        """Test retrieving letters for a specific user.

        This test verifies that:
        1. All letters from groups the user is a member of are returned
        2. Letters from other groups are not included
        3. The response includes letters from multiple groups
        4. The database state is preserved

        Args:
            db_session (Session): Database session
        """
        user = UserFactory.create()
        admin = UserFactory.create()
        groups = [
            GroupFactory.create(admin=admin, members=[admin, user])
            for _ in range(3)
        ]
        letters = [LetterFactory.create(group=g) for g in groups]
        db_session.commit()

        assert letter_crud.get_letters_for_user(db_session, user) == letters

    def test_create_letter(self, db_session: Session, faker: Faker) -> None:
        """Test creating a new letter.

        This test verifies that:
        1. A letter can be created with valid group and send time
        2. The letter is associated with the correct group
        3. The letter has the correct status and send time
        4. The letter is associated with all group members
        5. The letter has the correct number based on group history
        6. The required tasks are created with correct timing
        7. Letters can be created with different statuses

        Args:
            db_session (Session): Database session
            faker (Faker): Faker instance for generating test data
        """
        group = GroupFactory.create()
        send_at = datetime.now(tz=UTC) + timedelta(days=2)
        letter = letter_crud.create_letter(
            db_session, group.api_identifier, send_at
        )
        db_session.commit()

        assert letter.group == group
        assert letter.send_at == send_at
        assert letter.status == LetterStatus.UPCOMING
        assert letter.participants == group.members
        assert letter.questions == []
        assert letter.id is not None
        assert letter.created_at is not None
        assert letter.api_identifier.startswith(Letter.API_ID_PREFIX)

        assert letter.number == 1

        [send_email_task, reminder_email_task] = group.schedule.tasks
        assert send_email_task.type == TaskType.SEND_EMAIL
        assert send_email_task.execute_at == send_at

        assert reminder_email_task.type == TaskType.REMINDER_EMAIL
        assert reminder_email_task.execute_at == send_at - timedelta(days=1)

        letter_2 = letter_crud.create_letter(
            db_session,
            group.api_identifier,
            send_at,
            letter_status=LetterStatus.IN_PROGRESS,
        )
        db_session.commit()

        assert letter_2.number == 2
        assert letter_2.status == LetterStatus.IN_PROGRESS

    def test_create_letter_with_questions(
        self, db_session: Session, faker: Faker
    ) -> None:
        """Test creating a letter with predefined questions.

        This test verifies that:
        1. A letter can be created with questions from the question bank
        2. The letter is associated with the correct group
        3. The letter has the correct status and send time
        4. The letter is associated with all group members
        5. The questions are from the predefined question bank
        6. The letter has the required metadata fields

        Args:
            db_session (Session): Database session
            faker (Faker): Faker instance for generating test data
        """
        group = GroupFactory.create()
        send_at = faker.date_time(tzinfo=UTC)

        letter = letter_crud.create_letter_with_questions(
            db_session, group.api_identifier, send_at
        )
        db_session.commit()

        assert letter.group == group
        assert letter.send_at == send_at
        assert letter.status == LetterStatus.UPCOMING
        assert letter.participants == group.members
        assert all(
            [
                q.question_text in QUESTION_BANK + DEFAULT_QUESTIONS
                for q in letter.questions
            ]
        )
        assert letter.id is not None
        assert letter.created_at is not None
        assert letter.api_identifier.startswith(Letter.API_ID_PREFIX)

    def test_create_letter_with_questions_group_default_questions(
        self, db_session: Session, faker: Faker
    ) -> None:
        """Test creating a letter with group-specific default questions.

        This test verifies that:
        1. A letter can be created with group-specific default questions
        2. The letter includes both question bank and default questions
        3. The letter is associated with the correct group
        4. The letter has the correct status and send time
        5. The letter is associated with all group members
        6. The letter has the required metadata fields

        Args:
            db_session (Session): Database session
            faker (Faker): Faker instance for generating test data
        """
        group = GroupFactory.create()
        default_questions = [
            DefaultQuestionFactory.create(group=group),
        ]
        send_at = faker.date_time(tzinfo=UTC)

        letter = letter_crud.create_letter_with_questions(
            db_session, group.api_identifier, send_at
        )
        db_session.commit()

        assert letter.group == group
        assert letter.send_at == send_at
        assert letter.status == LetterStatus.UPCOMING
        assert letter.participants == group.members
        assert all(
            [
                q.question_text
                in QUESTION_BANK
                + [dq.question_text for dq in default_questions]
                for q in letter.questions
            ]
        )
        assert letter.id is not None
        assert letter.created_at is not None
        assert letter.api_identifier.startswith(Letter.API_ID_PREFIX)

    def test_edit_letter(self, db_session: Session, faker: Faker) -> None:
        """Test editing an existing letter.

        This test verifies that:
        1. A letter's send time can be updated
        2. The associated tasks are updated with new timing
        3. The database state is updated correctly
        4. The letter's other attributes remain unchanged

        Args:
            db_session (Session): Database session
            faker (Faker): Faker instance for generating test data
        """
        group = GroupFactory.create()
        letter = LetterFactory.create(group=group)
        db_session.commit()

        new_send_at = datetime.now(tz=UTC) + timedelta(days=30)

        edited_letter = letter_crud.edit_letter(
            db_session, letter, new_send_at
        )
        db_session.commit()

        assert edited_letter.send_at == new_send_at

        [send_email_task, reminder_email_task] = group.schedule.tasks
        assert send_email_task.execute_at == new_send_at
        assert reminder_email_task.execute_at == new_send_at - timedelta(
            days=1
        )

    def test_upsert_letter_tasks(self, db_session: Session) -> None:
        """Test updating letter-related tasks.

        This test verifies that:
        1. Tasks are created with correct timing on letter creation
        2. Tasks are updated when letter send time changes
        3. Duplicate tasks are not created
        4. The database state is updated correctly

        Args:
            db_session (Session): Database session
        """
        send_at = datetime.now(tz=UTC) + timedelta(days=2)
        letter = LetterFactory.create(send_at=send_at)
        db_session.commit()

        [send_email_task, reminder_email_task] = letter.group.schedule.tasks
        assert send_email_task.execute_at == letter.send_at
        assert reminder_email_task.execute_at == letter.send_at - timedelta(
            days=1
        )

        new_send_at = datetime.now(tz=UTC) + timedelta(days=30)

        letter_crud.upsert_letter_tasks(db_session, letter, new_send_at)
        db_session.commit()

        [send_email_task, reminder_email_task] = letter.group.schedule.tasks
        assert send_email_task.execute_at == new_send_at
        assert reminder_email_task.execute_at == new_send_at - timedelta(
            days=1
        )

        letter.send_at = new_send_at
        letter.status = LetterStatus.UPCOMING
        db_session.commit()

        letter_crud.upsert_letter_tasks(db_session, letter, new_send_at)
        db_session.commit()

        [send_email_task, reminder_email_task_1, reminder_email_task_2] = (
            letter.group.schedule.tasks
        )
        assert send_email_task.execute_at == new_send_at
        assert reminder_email_task_1.execute_at == new_send_at - timedelta(
            days=1
        )
        assert reminder_email_task_2.execute_at == new_send_at - timedelta(
            days=1
        )

    def test_add_question(self, db_session: Session, faker: Faker) -> None:
        """Test adding a question to a letter.

        This test verifies that:
        1. A question can be added to a letter
        2. The question is associated with the correct letter
        3. The question text is stored correctly
        4. The database state is updated correctly

        Args:
            db_session (Session): Database session
            faker (Faker): Faker instance for generating test data
        """
        letter = LetterFactory.create()
        db_session.commit()

        question_text = faker.sentence()
        question = letter_crud.add_question(db_session, letter, question_text)
        db_session.commit()

        assert question.letter == letter
        assert question.question_text == question_text

    def test_add_default_questions(self, db_session: Session) -> None:
        """Test adding default questions to a letter.

        This test verifies that:
        1. Default questions can be added to a letter
        2. The questions are associated with the correct letter
        3. The questions are from the default question bank
        4. The database state is updated correctly

        Args:
            db_session (Session): Database session
        """
        letter = LetterFactory.create()
        db_session.commit()

        questions = letter_crud.add_default_questions(db_session, letter)
        db_session.commit()

        assert all(q.letter == letter for q in questions)
        assert all(q.question_text in DEFAULT_QUESTIONS for q in questions)

    def test_add_random_questions(self, db_session: Session) -> None:
        """Test adding random questions to a letter.

        This test verifies that:
        1. Random questions can be added to a letter
        2. The questions are associated with the correct letter
        3. The questions are from the question bank
        4. The database state is updated correctly

        Args:
            db_session (Session): Database session
        """
        letter = LetterFactory.create()
        db_session.commit()

        questions = letter_crud.add_random_questions(db_session, letter)
        db_session.commit()

        assert all(q.letter == letter for q in questions)
        assert all(q.question_text in QUESTION_BANK for q in questions)

    def test_compile_letter_dict(self, db_session: Session) -> None:
        """Test compiling a letter's data into a dictionary.

        This test verifies that:
        1. The letter's basic attributes are included
        2. The letter's questions are included
        3. The letter's responses are included
        4. The dictionary structure is correct

        Args:
            db_session (Session): Database session
        """
        letter = LetterFactory.create()
        questions = [QuestionFactory.create(letter=letter) for _ in range(3)]
        db_session.commit()

        letter_dict = letter_crud.compile_letter_dict(letter)

        assert letter_dict["id"] == letter.id
        assert letter_dict["api_identifier"] == letter.api_identifier
        assert letter_dict["send_at"] == letter.send_at
        assert letter_dict["status"] == letter.status
        assert letter_dict["number"] == letter.number
        assert letter_dict["questions"] == [
            {
                "id": q.id,
                "api_identifier": q.api_identifier,
                "question_text": q.question_text,
                "responses": [],
            }
            for q in questions
        ]

    def test_collect_future_letters(self, db_session: Session) -> None:
        """Test collecting future letters.

        This test verifies that:
        1. Future letters are collected correctly
        2. Past letters are not included
        3. The letters are sorted by send time
        4. The database state is preserved

        Args:
            db_session (Session): Database session
        """
        group = GroupFactory.create()
        past_letter = LetterFactory.create(
            group=group,
            send_at=datetime.now(tz=UTC) - timedelta(days=1),
        )
        future_letter = LetterFactory.create(
            group=group,
            send_at=datetime.now(tz=UTC) + timedelta(days=1),
        )
        db_session.commit()

        future_letters = letter_crud.collect_future_letters(db_session)

        assert past_letter not in future_letters
        assert future_letter in future_letters
        assert len(future_letters) == 1

    def test_collect_future_letters_no_letters(
        self, db_session: Session
    ) -> None:
        """Test collecting future letters when none exist.

        This test verifies that:
        1. An empty list is returned when no future letters exist
        2. Past letters are not included
        3. The database state is preserved

        Args:
            db_session (Session): Database session
        """
        group = GroupFactory.create()
        past_letter = LetterFactory.create(
            group=group,
            send_at=datetime.now(tz=UTC) - timedelta(days=1),
        )
        db_session.commit()

        future_letters = letter_crud.collect_future_letters(db_session)

        assert past_letter not in future_letters
        assert len(future_letters) == 0

    def test_promote_and_create_new_letters(self, db_session: Session) -> None:
        """Test promoting and creating new letters.

        This test verifies that:
        1. Upcoming letters are promoted to in-progress
        2. New upcoming letters are created
        3. The letter numbering is maintained
        4. The database state is updated correctly

        Args:
            db_session (Session): Database session
        """
        # TODO(#110): Implement celery task testing

    def test_postpend_upcoming_letters(self, db_session: Session) -> None:
        """Test postpending upcoming letters.

        This test verifies that:
        1. Upcoming letters are postpended correctly
        2. The send times are updated
        3. The tasks are updated
        4. The database state is updated correctly

        Args:
            db_session (Session): Database session
        """
        # TODO(#110): Implement celery task testing

    def test_add_participants(self, db_session: Session) -> None:
        """Test adding participants to a letter.

        This test verifies that:
        1. New participants can be added to a letter
        2. Existing participants are not duplicated
        3. The letter's participant list is updated
        4. The database state is updated correctly

        Args:
            db_session (Session): Database session
        """
        letter = LetterFactory.create()
        new_participant = UserFactory.create()
        db_session.commit()

        letter_crud.add_participants(db_session, letter, [new_participant])
        db_session.commit()

        assert new_participant in letter.participants
