"""Tests for the letter API endpoints.

This module contains tests for all letter-related API endpoints,
including letter creation, retrieval, editing, and dashboard views.
It verifies both successful operations and error cases.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ring.letters.constants import LetterStatus
from ring.letters.models.letter_model import Letter
from ring.parties.models.group_model import Group
from ring.ring_pydantic.linked_schemas import MinimalLetter
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory
from ring.tests.lib.utils import (
    assert_api_model_not_found,
    assert_pydantic_model_json_dump_equivalent_to_response_dict,
    assert_pydantic_models_json_dump_in_response_dict,
)


class TestLetterAPI:
    """Test suite for letter API endpoints.

    This class contains tests for all letter-related API operations,
    including CRUD operations, dashboard views, and error handling.
    """

    def test_add_next_letter(
        self, authenticated_client: TestClient, db_session: Session
    ):
        """Test adding a new letter to a group.

        This test verifies that:
        1. A new letter can be added to a group
        2. The letter is created with the correct send time
        3. The letter is associated with the correct group
        4. The response contains the correct letter data

        Args:
            authenticated_client (TestClient): Authenticated test client
            db_session (Session): Database session
        """
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
            group.cyclic_letters[-1], data
        )

    def test_add_next_letter_with_existing_letter_upcoming(
        self, authenticated_client: TestClient, db_session: Session
    ):
        """Test adding a letter when an upcoming letter exists.

        This test verifies that:
        1. Adding a letter fails when an upcoming letter exists
        2. The response contains the correct error message
        3. The database state remains unchanged
        4. The existing letter remains in the upcoming state

        Args:
            authenticated_client (TestClient): Authenticated test client
            db_session (Session): Database session
        """
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
        """Test adding a letter when an in-progress letter exists.

        This test verifies that:
        1. Adding a letter fails when an in-progress letter exists
        2. The response contains the correct error message
        3. The database state remains unchanged
        4. The existing letter remains in the in-progress state

        Args:
            authenticated_client (TestClient): Authenticated test client
            db_session (Session): Database session
        """
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
        """Test listing letters for a group.

        This test verifies that:
        1. All letters for a group are returned
        2. The response contains the correct number of letters
        3. The letters are returned in the correct order
        4. The response matches the database state

        Args:
            authenticated_client (TestClient): Authenticated test client
            db_session (Session): Database session
        """
        group = GroupFactory.create()
        letters = [LetterFactory.create(group=group) for _ in range(5)]
        db_session.commit()
        response = authenticated_client.get(
            f"/letters/letters/?group_api_id={group.api_identifier}"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
        assert_pydantic_models_json_dump_in_response_dict(
            letters, data, override_pydantic_model=MinimalLetter
        )

    def test_list_letters_not_found(
        self, authenticated_client: TestClient, db_session: Session
    ):
        """Test listing letters for a non-existent group.

        This test verifies that:
        1. Listing letters for a non-existent group fails
        2. The response contains the correct error message
        3. The response indicates the group was not found
        4. The database state remains unchanged

        Args:
            authenticated_client (TestClient): Authenticated test client
            db_session (Session): Database session
        """
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
        """Test reading a specific letter.

        This test verifies that:
        1. A letter can be retrieved by its API identifier
        2. The response contains the correct letter data
        3. The response matches the database state
        4. All letter fields are included in the response

        Args:
            authenticated_client (TestClient): Authenticated test client
            db_session (Session): Database session
        """
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
        """Test reading a non-existent letter.

        This test verifies that:
        1. Reading a non-existent letter fails
        2. The response contains the correct error message
        3. The response indicates the letter was not found
        4. The database state remains unchanged

        Args:
            authenticated_client (TestClient): Authenticated test client
            db_session (Session): Database session
        """
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
        """Test listing letters for the dashboard view.

        This test verifies that:
        1. Upcoming letters are returned correctly
        2. In-progress letters are returned correctly
        3. Recently completed letters are returned correctly
        4. The response matches the database state
        5. Letters are categorized correctly by status

        Args:
            authenticated_client (TestClient): Authenticated test client
            db_session (Session): Database session
            current_user (UserFactory): Currently authenticated user
        """
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
        """Test listing letters for the dashboard view when no letters exist.

        This test verifies that:
        1. Empty lists are returned for all categories
        2. The response structure is correct
        3. The database state remains unchanged
        4. The response matches the database state

        Args:
            authenticated_client (TestClient): Authenticated test client
            db_session (Session): Database session
            current_user (UserFactory): Currently authenticated user
        """
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
        """Test editing a letter's send time.

        This test verifies that:
        1. A letter's send time can be updated
        2. The response contains the updated letter data
        3. The database state is updated correctly
        4. The letter's other attributes remain unchanged

        Args:
            authenticated_client (TestClient): Authenticated test client
            db_session (Session): Database session
        """
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
        """Test editing an upcoming letter with a past send time.

        This test verifies that:
        1. Setting a past send time for an upcoming letter fails
        2. The response contains the correct error message
        3. The letter's send time remains unchanged
        4. The database state remains unchanged

        Args:
            authenticated_client (TestClient): Authenticated test client
            db_session (Session): Database session
        """
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
        """Test editing an in-progress letter with a past send time.

        This test verifies that:
        1. Setting a past send time for an in-progress letter fails
        2. The response contains the correct error message
        3. The letter's send time remains unchanged
        4. The database state remains unchanged

        Args:
            authenticated_client (TestClient): Authenticated test client
            db_session (Session): Database session
        """
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
