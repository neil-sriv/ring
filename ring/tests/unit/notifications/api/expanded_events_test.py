"""API-level tests for expanded notification event wiring.

This module verifies that content and membership mutations (adding
questions, answering questions, joining groups) fan out the right in-app
notifications to the right users.
"""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ring.letters.constants import LetterStatus
from ring.notifications.constants import NotificationType
from ring.notifications.crud.notification import list_notifications
from ring.parties.crud.user import get_user_by_email
from ring.parties.models.user_model import User
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.letters.question_factory import QuestionFactory
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.invite_factory import InviteFactory
from ring.tests.factories.parties.user_factory import UserFactory


class TestExpandedEventApiWiring:
    """New-question, new-response, and member-joined wiring."""

    def test_add_question_notifies_other_participants(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ) -> None:
        others = [UserFactory.create() for _ in range(2)]
        group = GroupFactory.create(
            admin=current_user, members=[current_user, *others]
        )
        letter = LetterFactory.create(
            group=group, status=LetterStatus.IN_PROGRESS
        )
        db_session.commit()

        response = authenticated_client.post(
            f"/letters/letter/{letter.api_identifier}:add_question",
            json={
                "question_text": "What made you laugh this week?",
                "author_api_id": None,
            },
        )

        assert response.status_code == 200
        assert list_notifications(db_session, current_user) == []
        for other in others:
            notifications = list_notifications(db_session, other)
            assert [n.type for n in notifications] == [
                NotificationType.NEW_QUESTION
            ]
            assert "laugh this week" in notifications[0].body

    def test_upsert_response_notifies_question_author_once(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ) -> None:
        author = UserFactory.create()
        group = GroupFactory.create(
            admin=author, members=[author, current_user]
        )
        letter = LetterFactory.create(
            group=group, status=LetterStatus.IN_PROGRESS
        )
        question = QuestionFactory.create(letter=letter, author=author)
        db_session.commit()

        create_response = authenticated_client.post(
            f"/questions/question/{question.api_identifier}:upsert_response",
            json={
                "response_text": "It was the picnic!",
                "participant_api_identifier": current_user.api_identifier,
            },
        )
        assert create_response.status_code == 200

        notifications = list_notifications(db_session, author)
        assert [n.type for n in notifications] == [
            NotificationType.NEW_RESPONSE
        ]
        assert (current_user.name or current_user.email) in notifications[
            0
        ].title

        # Editing the same answer must not re-notify.
        edit_response = authenticated_client.post(
            f"/questions/question/{question.api_identifier}:upsert_response",
            json={
                "response_text": "Actually, the bonfire.",
                "participant_api_identifier": current_user.api_identifier,
            },
        )
        assert edit_response.status_code == 200
        assert len(list_notifications(db_session, author)) == 1

    def test_register_via_invite_notifies_existing_members(
        self,
        unauthenticated_client: TestClient,
        db_session: Session,
    ) -> None:
        admin = UserFactory.create()
        member = UserFactory.create()
        group = GroupFactory.create(admin=admin, members=[admin, member])
        invite = InviteFactory.create(
            group=group, inviter=admin, email="newbie@example.com"
        )
        db_session.commit()

        response = unauthenticated_client.post(
            f"/parties/register/{invite.one_time_token.token}",
            json={
                "name": "New Bee",
                "email": "newbie@example.com",
                "password": "supersafepassword",
            },
        )

        assert response.status_code == 200
        new_user = get_user_by_email(db_session, "newbie@example.com")
        assert new_user is not None
        assert list_notifications(db_session, new_user) == []
        for existing in (admin, member):
            notifications = list_notifications(db_session, existing)
            assert [n.type for n in notifications] == [
                NotificationType.MEMBER_JOINED
            ]
            assert "New Bee" in notifications[0].title

    def test_add_single_member_notifies_and_is_idempotent(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ) -> None:
        existing = UserFactory.create()
        group = GroupFactory.create(
            admin=current_user, members=[current_user, existing]
        )
        new_user = UserFactory.create()
        db_session.commit()

        response = authenticated_client.post(
            f"/parties/group/{group.api_identifier}:add_member/"
            f"{new_user.api_identifier}"
        )
        assert response.status_code == 200

        assert [n.type for n in list_notifications(db_session, new_user)] == [
            NotificationType.ADDED_TO_GROUP
        ]
        assert [n.type for n in list_notifications(db_session, existing)] == [
            NotificationType.MEMBER_JOINED
        ]
        assert list_notifications(db_session, current_user) == []

        # Adding an existing member again must not re-notify anyone.
        repeat = authenticated_client.post(
            f"/parties/group/{group.api_identifier}:add_member/"
            f"{new_user.api_identifier}"
        )
        assert repeat.status_code == 200
        assert len(list_notifications(db_session, new_user)) == 1
        assert len(list_notifications(db_session, existing)) == 1
