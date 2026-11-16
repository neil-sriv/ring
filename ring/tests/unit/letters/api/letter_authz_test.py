"""Authz coverage for letter create / edit / read / add-question.

The UI already hides Start Next Loop and Edit Loop from non-admins. These
tests pin the matching API gates so membership and admin checks stay enforced
even when a caller hits the endpoints directly.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy.orm import Session

from ring.authz.grants import grant_permission
from ring.authz.permission_grant import Permission, PermissionGrant
from ring.letters.constants import LetterStatus, LetterType
from ring.parties.models.user_model import User
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory


def _send_at_payload(group_api_id: str) -> dict[str, str]:
    return {
        "group_api_identifier": group_api_id,
        "send_at": (datetime.now(tz=UTC) + timedelta(days=2)).isoformat(),
    }


class TestLetterAuthz:
    def test_non_member_cannot_create_next_letter(
        self,
        authenticated_client: TestClient,
        db_session: Session,
    ) -> None:
        group = GroupFactory.create()
        db_session.commit()

        response = authenticated_client.post(
            "/letters/letter",
            json=_send_at_payload(group.api_identifier),
        )

        assert response.status_code == 403
        assert response.json()["detail"] == (
            "Not authorized to access this resource"
        )

    def test_non_admin_member_cannot_create_next_letter(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ) -> None:
        admin = UserFactory.create()
        group = GroupFactory.create(admin=admin, members=[admin, current_user])
        db_session.commit()

        response = authenticated_client.post(
            "/letters/letter",
            json=_send_at_payload(group.api_identifier),
        )

        assert response.status_code == 403
        assert response.json()["detail"] == (
            "Not authorized to create the next letter"
        )

    def test_non_admin_member_cannot_create_cyclic_typed(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ) -> None:
        admin = UserFactory.create()
        group = GroupFactory.create(admin=admin, members=[admin, current_user])
        db_session.commit()

        response = authenticated_client.post(
            "/letters/letter:CYCLIC",
            json=_send_at_payload(group.api_identifier),
        )

        assert response.status_code == 403
        assert response.json()["detail"] == (
            "Not authorized to create the next letter"
        )

    def test_member_can_create_adhoc_letter(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ) -> None:
        admin = UserFactory.create()
        group = GroupFactory.create(admin=admin, members=[admin, current_user])
        db_session.commit()

        response = authenticated_client.post(
            "/letters/letter:ADHOC",
            json={
                **_send_at_payload(group.api_identifier),
                "title": "Off cycle",
            },
        )

        assert response.status_code == 200
        assert response.json()["letter_type"] == "ADHOC"

    def test_non_admin_member_cannot_edit_letter(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ) -> None:
        admin = UserFactory.create()
        group = GroupFactory.create(admin=admin, members=[admin, current_user])
        letter = LetterFactory.create(
            group=group, status=LetterStatus.UPCOMING
        )
        db_session.commit()
        original_send_at = letter.send_at

        response = authenticated_client.post(
            f"/letters/letter/{letter.api_identifier}:edit_letter",
            json={
                "send_at": (
                    datetime.now(tz=UTC) + timedelta(days=30)
                ).isoformat()
            },
        )

        assert response.status_code == 403
        assert response.json()["detail"] == (
            "Not authorized to edit this letter"
        )
        db_session.refresh(letter)
        assert letter.send_at == original_send_at

    def test_non_member_cannot_read_letter(
        self,
        authenticated_client: TestClient,
        db_session: Session,
    ) -> None:
        letter = LetterFactory.create(status=LetterStatus.UPCOMING)
        db_session.commit()

        response = authenticated_client.get(
            f"/letters/letter/{letter.api_identifier}"
        )

        assert response.status_code == 403
        assert response.json()["detail"] == (
            "Not authorized to access this resource"
        )

    def test_non_member_cannot_add_question(
        self,
        authenticated_client: TestClient,
        db_session: Session,
    ) -> None:
        letter = LetterFactory.create(status=LetterStatus.UPCOMING)
        db_session.commit()

        response = authenticated_client.post(
            f"/letters/letter/{letter.api_identifier}:add_question",
            json={
                "question_text": "Should not land",
                "author_api_id": None,
            },
        )

        assert response.status_code == 403
        assert response.json()["detail"] == (
            "Not authorized to access this resource"
        )
        db_session.refresh(letter)
        assert all(
            q.question_text != "Should not land" for q in letter.questions
        )

    def test_non_member_cannot_list_letters(
        self,
        authenticated_client: TestClient,
        db_session: Session,
    ) -> None:
        group = GroupFactory.create()
        LetterFactory.create(group=group, status=LetterStatus.SENT)
        db_session.commit()

        response = authenticated_client.get(
            f"/letters/letters/?group_api_id={group.api_identifier}"
        )

        assert response.status_code == 403
        assert response.json()["detail"] == (
            "Not authorized to access this resource"
        )


def _edit(client: TestClient, letter_api_id: str):
    return client.post(
        f"/letters/letter/{letter_api_id}:edit_letter",
        json={
            "title": "Renamed",
            "send_at": (datetime.now(tz=UTC) + timedelta(days=30)).isoformat(),
        },
    )


class TestLetterPermissionGrants:
    """Manage checks read grants, not group.admin."""

    def test_group_admin_can_edit_any_loop(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ) -> None:
        group = GroupFactory.create(admin=current_user)
        cyclic = LetterFactory.create(
            group=group, status=LetterStatus.UPCOMING
        )
        adhoc = LetterFactory.create(
            group=group,
            status=LetterStatus.UPCOMING,
            letter_type=LetterType.ADHOC,
            number=None,
            title="Side",
        )
        db_session.commit()

        assert (
            _edit(authenticated_client, cyclic.api_identifier).status_code
            == 200
        )
        assert (
            _edit(authenticated_client, adhoc.api_identifier).status_code
            == 200
        )

    def test_member_cannot_edit_another_members_loop(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ) -> None:
        admin = UserFactory.create()
        owner = UserFactory.create()
        group = GroupFactory.create(
            admin=admin, members=[admin, current_user, owner]
        )
        own = LetterFactory.create(
            group=group,
            status=LetterStatus.UPCOMING,
            letter_type=LetterType.ADHOC,
            number=None,
        )
        theirs = LetterFactory.create(
            group=group,
            status=LetterStatus.UPCOMING,
            letter_type=LetterType.ADHOC,
            number=None,
        )
        db_session.flush()
        grant_permission(
            db_session,
            current_user.api_identifier,
            own.api_identifier,
            Permission.ADMIN,
        )
        db_session.commit()

        assert (
            _edit(authenticated_client, own.api_identifier).status_code == 200
        )
        denied = _edit(authenticated_client, theirs.api_identifier)
        assert denied.status_code == 403
        assert denied.json()["detail"] == "Not authorized to edit this letter"

    def test_member_group_admin_grant_covers_loops_without_role(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ) -> None:
        admin = UserFactory.create()
        group = GroupFactory.create(admin=admin, members=[admin, current_user])
        letter = LetterFactory.create(
            group=group, status=LetterStatus.UPCOMING
        )
        db_session.flush()
        assert current_user != group.admin
        grant_permission(
            db_session,
            current_user.api_identifier,
            group.api_identifier,
            Permission.ADMIN,
        )
        db_session.commit()

        assert (
            _edit(authenticated_client, letter.api_identifier).status_code
            == 200
        )

    def test_role_admin_without_grant_cannot_edit(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ) -> None:
        group = GroupFactory.create(admin=current_user)
        letter = LetterFactory.create(
            group=group, status=LetterStatus.UPCOMING
        )
        db_session.flush()
        db_session.execute(
            delete(PermissionGrant).where(
                PermissionGrant.subject_api_id == current_user.api_identifier,
                PermissionGrant.resource_api_id == group.api_identifier,
            )
        )
        db_session.commit()

        denied = _edit(authenticated_client, letter.api_identifier)
        assert denied.status_code == 403
        assert denied.json()["detail"] == "Not authorized to edit this letter"

    def test_non_member_cannot_edit_letter(
        self,
        authenticated_client: TestClient,
        db_session: Session,
    ) -> None:
        letter = LetterFactory.create(status=LetterStatus.UPCOMING)
        db_session.commit()

        denied = _edit(authenticated_client, letter.api_identifier)
        assert denied.status_code == 403
        assert denied.json()["detail"] == (
            "Not authorized to access this resource"
        )

    def test_loop_admin_cannot_create_cyclic_letter(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ) -> None:
        admin = UserFactory.create()
        group = GroupFactory.create(admin=admin, members=[admin, current_user])
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.UPCOMING,
            letter_type=LetterType.ADHOC,
            number=None,
        )
        db_session.flush()
        grant_permission(
            db_session,
            current_user.api_identifier,
            letter.api_identifier,
            Permission.ADMIN,
        )
        db_session.commit()

        response = authenticated_client.post(
            "/letters/letter",
            json=_send_at_payload(group.api_identifier),
        )
        assert response.status_code == 403
        assert response.json()["detail"] == (
            "Not authorized to create the next letter"
        )
