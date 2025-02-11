from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ring.letters.constants import LetterStatus
from ring.letters.models.letter_model import Letter
from ring.parties.models.group_model import Group
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory
from ring.tests.lib.utils import (
    assert_api_model_not_found,
    assert_pydantic_model_json_dump_equivalent_to_response_dict,
    assert_pydantic_models_json_dump_in_response_dict,
)


class TestLetterAPI:
    def test_add_next_letter(
        self, authenticated_client: TestClient, db_session: Session
    ):
        group = GroupFactory.create()
        db_session.commit()
        send_at = datetime.now(tz=UTC) + timedelta(days=2)
        input = {
            "group_api_identifier": group.api_identifier,
            "send_at": send_at.isoformat(),
        }
        response = authenticated_client.post("/letters/letter", json=input)
        assert response.status_code == 200
        data = response.json()
        assert data["group"]["api_identifier"] == group.api_identifier
        assert datetime.fromisoformat(data["send_at"]) == send_at
        assert_pydantic_model_json_dump_equivalent_to_response_dict(
            group.letters[-1], data
        )

    def test_add_next_letter_with_existing_letter_upcoming(
        self, authenticated_client: TestClient, db_session: Session
    ):
        group = GroupFactory.create()
        LetterFactory.create(group=group, status=LetterStatus.UPCOMING)
        db_session.commit()
        send_at = datetime.now(tz=UTC) + timedelta(days=2)
        input = {
            "group_api_identifier": group.api_identifier,
            "send_at": send_at.isoformat(),
        }
        with pytest.raises(
            ValueError,
            match="There is already a letter in progress or upcoming for this group",
        ):
            authenticated_client.post("/letters/letter", json=input)

    def test_add_next_letter_with_existing_letter_in_progress(
        self, authenticated_client: TestClient, db_session: Session
    ):
        group = GroupFactory.create()
        LetterFactory.create(group=group, status=LetterStatus.IN_PROGRESS)
        db_session.commit()
        send_at = datetime.now(tz=UTC) + timedelta(days=2)
        input = {
            "group_api_identifier": group.api_identifier,
            "send_at": send_at.isoformat(),
        }
        with pytest.raises(
            ValueError,
            match="There is already a letter in progress or upcoming for this group",
        ):
            authenticated_client.post("/letters/letter", json=input)

    def test_list_letters(
        self, authenticated_client: TestClient, db_session: Session
    ):
        group = GroupFactory.create()
        letters = [LetterFactory.create(group=group) for _ in range(5)]
        db_session.commit()
        response = authenticated_client.get(
            f"/letters/letters/?group_api_id={group.api_identifier}"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
        assert_pydantic_models_json_dump_in_response_dict(letters, data)

    def test_list_letters_not_found(
        self, authenticated_client: TestClient, db_session: Session
    ):
        db_session.commit()
        response = authenticated_client.get(
            "/letters/letters/?group_api_id=invalid-group"
        )
        assert response.status_code == 404
        data = response.json()
        assert_api_model_not_found(data, Group, ["invalid-group"])

    def test_read_letter(
        self, authenticated_client: TestClient, db_session: Session
    ):
        letter = LetterFactory.create()
        db_session.commit()
        response = authenticated_client.get(
            f"/letters/letter/{letter.api_identifier}"
        )
        assert response.status_code == 200
        data = response.json()
        assert_pydantic_model_json_dump_equivalent_to_response_dict(
            letter, data
        )

    def test_read_letter_not_found(
        self, authenticated_client: TestClient, db_session: Session
    ):
        db_session.commit()
        response = authenticated_client.get("/letters/letter/invalid-letter")
        assert response.status_code == 404
        data = response.json()
        assert_api_model_not_found(data, Letter, ["invalid-letter"])

    def test_list_dashboard_letters(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: UserFactory,
    ):
        group = GroupFactory.create(admin=current_user, members=[current_user])
        letters = [
            LetterFactory.create(group=group, status=LetterStatus.UPCOMING),
            LetterFactory.create(group=group, status=LetterStatus.IN_PROGRESS),
            LetterFactory.create(
                group=group,
                status=LetterStatus.SENT,
                send_at=datetime.now(tz=UTC) - timedelta(days=1),
            ),
        ]
        db_session.commit()
        response = authenticated_client.get("/letters/letters:dashboard")
        assert response.status_code == 200
        data = response.json()
        assert len(data["upcoming"]) == 1
        assert_pydantic_model_json_dump_equivalent_to_response_dict(
            letters[0], data["upcoming"][0]
        )
        assert len(data["in_progress"]) == 1
        assert_pydantic_model_json_dump_equivalent_to_response_dict(
            letters[1], data["in_progress"][0]
        )
        assert len(data["recently_completed"]) == 1
        assert_pydantic_model_json_dump_equivalent_to_response_dict(
            letters[2], data["recently_completed"][0]
        )

    def test_list_dashboard_letters_empty(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: UserFactory,
    ):
        GroupFactory.create(admin=current_user, members=[current_user])
        db_session.commit()
        response = authenticated_client.get("/letters/letters:dashboard")
        assert response.status_code == 200
        data = response.json()
        assert data["upcoming"] == []
        assert data["in_progress"] == []
        assert data["recently_completed"] == []

    def test_edit_letter(
        self, authenticated_client: TestClient, db_session: Session
    ):
        letter = LetterFactory.create(status=LetterStatus.UPCOMING)
        db_session.commit()
        new_send_at = datetime.now(tz=UTC) + timedelta(days=30)
        input = {"send_at": new_send_at.isoformat()}
        response = authenticated_client.post(
            f"/letters/letter/{letter.api_identifier}:edit_letter", json=input
        )
        assert response.status_code == 200
        data = response.json()
        assert datetime.fromisoformat(data["send_at"]) == new_send_at

    def test_edit_letter_upcoming_invalid_past_send_at(
        self, authenticated_client: TestClient, db_session: Session
    ):
        letter = LetterFactory.create(status=LetterStatus.UPCOMING)
        db_session.commit()
        input = {"send_at": datetime.now(tz=UTC).isoformat()}

        with pytest.raises(AssertionError):
            authenticated_client.post(
                f"/letters/letter/{letter.api_identifier}:edit_letter",
                json=input,
            )

    def test_edit_letter_in_progress_invalid_past_send_at(
        self, authenticated_client: TestClient, db_session: Session
    ):
        letter = LetterFactory.create(status=LetterStatus.IN_PROGRESS)
        db_session.commit()
        input = {"send_at": datetime.now(tz=UTC).isoformat()}

        with pytest.raises(AssertionError):
            authenticated_client.post(
                f"/letters/letter/{letter.api_identifier}:edit_letter",
                json=input,
            )

    def test_edit_letter_upcoming_conflicting_in_progress_send_at(
        self, authenticated_client: TestClient, db_session: Session
    ):
        letter = LetterFactory.create(status=LetterStatus.UPCOMING)
        in_progress_letter = LetterFactory.create(
            group=letter.group, status=LetterStatus.IN_PROGRESS
        )
        db_session.commit()
        input = {
            "send_at": (
                in_progress_letter.send_at - timedelta(days=1)
            ).isoformat()
        }

        with pytest.raises(AssertionError):
            authenticated_client.post(
                f"/letters/letter/{letter.api_identifier}:edit_letter",
                json=input,
            )

    def test_add_question(
        self, authenticated_client: TestClient, db_session: Session
    ):
        letter = LetterFactory.create()
        user = UserFactory.create()
        db_session.commit()
        input = {
            "question_text": "What is your favorite color?",
            "author_api_id": user.api_identifier,
        }
        response = authenticated_client.post(
            f"/letters/letter/{letter.api_identifier}:add_question", json=input
        )
        assert response.status_code == 200
        data = response.json()
        assert any(
            q["question_text"] == "What is your favorite color?"
            for q in data["questions"]
        )
