"""Tests for the share link API endpoints and their authorization."""

from __future__ import annotations

from sqlalchemy.orm import Session

from ring.sharing.crud import share_link as share_link_crud
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory
from ring.tests.unit.conftest import TClientForUser


class TestCreateShareLink:
    """Test suite for POST /shares/."""

    def test_member_can_mint_a_link(
        self,
        get_client_for_user: TClientForUser,
        db_session: Session,
    ) -> None:
        member = UserFactory.create()
        group = GroupFactory.create(admin=member)
        letter = LetterFactory.create(group=group)
        db_session.commit()

        client = get_client_for_user(member)
        response = client.post(
            "/shares/", json={"target_api_id": letter.api_identifier}
        )

        assert response.status_code == 200
        body = response.json()
        assert body["target_api_id"] == letter.api_identifier
        assert body["token"].startswith("sh_")
        assert f"/loops/{letter.api_identifier}" in body["share_url"]
        assert f"s={body['token']}" in body["share_url"]

    def test_minting_is_idempotent(
        self,
        get_client_for_user: TClientForUser,
        db_session: Session,
    ) -> None:
        member = UserFactory.create()
        group = GroupFactory.create(admin=member)
        letter = LetterFactory.create(group=group)
        db_session.commit()

        client = get_client_for_user(member)
        first = client.post(
            "/shares/", json={"target_api_id": letter.api_identifier}
        ).json()
        second = client.post(
            "/shares/", json={"target_api_id": letter.api_identifier}
        ).json()

        assert first["token"] == second["token"]

    def test_non_member_is_forbidden(
        self,
        get_client_for_user: TClientForUser,
        db_session: Session,
    ) -> None:
        outsider = UserFactory.create()
        group = GroupFactory.create()
        letter = LetterFactory.create(group=group)
        db_session.commit()

        client = get_client_for_user(outsider)
        response = client.post(
            "/shares/", json={"target_api_id": letter.api_identifier}
        )

        assert response.status_code == 403
        # No link should have been minted for a resource the user can't see.
        assert (
            share_link_crud.get_share_link_for_target(
                db_session, letter.api_identifier
            )
            is None
        )

    def test_missing_target_is_forbidden_not_leaked(
        self,
        get_client_for_user: TClientForUser,
        db_session: Session,
    ) -> None:
        """A nonexistent id returns 403, not 404, so existence stays hidden."""
        member = UserFactory.create()
        db_session.commit()

        client = get_client_for_user(member)
        response = client.post(
            "/shares/", json={"target_api_id": "lttr_does-not-exist"}
        )

        assert response.status_code == 403


class TestGetShareLink:
    """Test suite for GET /shares/."""

    def test_returns_existing_link(
        self,
        get_client_for_user: TClientForUser,
        db_session: Session,
    ) -> None:
        member = UserFactory.create()
        group = GroupFactory.create(admin=member)
        letter = LetterFactory.create(group=group)
        db_session.commit()
        client = get_client_for_user(member)
        client.post("/shares/", json={"target_api_id": letter.api_identifier})

        response = client.get(
            "/shares/", params={"target_api_id": letter.api_identifier}
        )

        assert response.status_code == 200
        assert response.json()["target_api_id"] == letter.api_identifier

    def test_404_when_no_link_yet(
        self,
        get_client_for_user: TClientForUser,
        db_session: Session,
    ) -> None:
        member = UserFactory.create()
        group = GroupFactory.create(admin=member)
        letter = LetterFactory.create(group=group)
        db_session.commit()

        client = get_client_for_user(member)
        response = client.get(
            "/shares/", params={"target_api_id": letter.api_identifier}
        )

        assert response.status_code == 404


class TestRevokeShareLink:
    """Test suite for DELETE /shares/{token}."""

    def test_member_can_revoke(
        self,
        get_client_for_user: TClientForUser,
        db_session: Session,
    ) -> None:
        member = UserFactory.create()
        group = GroupFactory.create(admin=member)
        letter = LetterFactory.create(group=group)
        db_session.commit()
        client = get_client_for_user(member)
        token = client.post(
            "/shares/", json={"target_api_id": letter.api_identifier}
        ).json()["token"]

        response = client.delete(f"/shares/{token}")

        assert response.status_code == 204
        assert (
            share_link_crud.get_share_link_by_token(db_session, token) is None
        )

    def test_non_member_cannot_revoke(
        self,
        get_client_for_user: TClientForUser,
        db_session: Session,
    ) -> None:
        member = UserFactory.create()
        group = GroupFactory.create(admin=member)
        letter = LetterFactory.create(group=group)
        db_session.commit()
        link = share_link_crud.get_or_create_share_link(
            db_session,
            target_api_id=letter.api_identifier,
            created_by_api_id=member.api_identifier,
        )
        db_session.commit()

        outsider = UserFactory.create()
        db_session.commit()
        client = get_client_for_user(outsider)
        response = client.delete(f"/shares/{link.token}")

        assert response.status_code == 403
        assert (
            share_link_crud.get_share_link_by_token(db_session, link.token)
            is not None
        )

    def test_revoking_unknown_token_is_404(
        self,
        get_client_for_user: TClientForUser,
        db_session: Session,
    ) -> None:
        member = UserFactory.create()
        db_session.commit()

        client = get_client_for_user(member)
        response = client.delete("/shares/sh_unknown")

        assert response.status_code == 404
