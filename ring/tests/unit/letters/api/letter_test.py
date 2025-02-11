from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ring.letters.constants import LetterStatus
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory
from ring.tests.lib.utils import (
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
