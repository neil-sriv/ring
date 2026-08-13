"""Tests for the short link API endpoints.

Covers creation (with authorization), idempotent reuse, resolution, and
revocation of short links, plus the error paths for unshareable targets,
unauthenticated access, and permission denial.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ring.letters.constants import LetterStatus
from ring.links.models.short_link_model import ShortLink
from ring.parties.models.user_model import User
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.links.short_link_factory import ShortLinkFactory
from ring.tests.factories.parties.group_factory import GroupFactory


class TestCreateShortLink:
    """Tests for creating short links."""

    @pytest.mark.parametrize(
        "status",
        [LetterStatus.UPCOMING, LetterStatus.IN_PROGRESS, LetterStatus.SENT],
    )
    def test_create_short_link_for_letter(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
        status: LetterStatus,
    ) -> None:
        """A group member can create a short link for a letter (draft or sent)."""
        group = GroupFactory.create(admin=current_user)
        letter = LetterFactory.create(group=group, status=status)
        db_session.commit()

        response = authenticated_client.post(
            "/links/short-link",
            json={"target_api_id": letter.api_identifier},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["target_api_id"] == letter.api_identifier
        assert data["target_type"] == "letter"
        assert data["token"]
        assert data["path"] == f"/s/{data['token']}"
        assert data["api_identifier"].startswith("shl_")

        db_link = db_session.query(ShortLink).one()
        assert db_link.token == data["token"]
        assert db_link.target_api_id == letter.api_identifier
        assert db_link.creator_id == current_user.id

    def test_create_short_link_is_idempotent(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ) -> None:
        """Repeated share actions reuse the same link rather than minting new ones."""
        group = GroupFactory.create(admin=current_user)
        letter = LetterFactory.create(group=group)
        db_session.commit()

        first = authenticated_client.post(
            "/links/short-link",
            json={"target_api_id": letter.api_identifier},
        )
        second = authenticated_client.post(
            "/links/short-link",
            json={"target_api_id": letter.api_identifier},
        )

        assert first.status_code == 201
        assert second.status_code == 201
        assert first.json()["token"] == second.json()["token"]
        assert (
            first.json()["api_identifier"] == second.json()["api_identifier"]
        )
        assert db_session.query(ShortLink).count() == 1

    def test_create_short_link_unshareable_target(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ) -> None:
        """Targets whose type is not shareable are rejected with a 400."""
        group = GroupFactory.create(admin=current_user)
        db_session.commit()

        response = authenticated_client.post(
            "/links/short-link",
            json={"target_api_id": group.api_identifier},
        )

        assert response.status_code == 400
        assert db_session.query(ShortLink).count() == 0

    def test_create_short_link_permission_denied(
        self,
        authenticated_client: TestClient,
        db_session: Session,
    ) -> None:
        """A user cannot mint a link for a letter they cannot read."""
        # Letter belongs to a group the authenticated user is not a member of.
        letter = LetterFactory.create()
        db_session.commit()

        with pytest.raises(PermissionError):
            authenticated_client.post(
                "/links/short-link",
                json={"target_api_id": letter.api_identifier},
            )
        assert db_session.query(ShortLink).count() == 0

    def test_create_short_link_unauthenticated(
        self,
        unauthenticated_client: TestClient,
        db_session: Session,
    ) -> None:
        """Creating a short link requires authentication."""
        letter = LetterFactory.create()
        db_session.commit()

        response = unauthenticated_client.post(
            "/links/short-link",
            json={"target_api_id": letter.api_identifier},
        )
        assert response.status_code == 401


class TestResolveShortLink:
    """Tests for resolving short links."""

    def test_resolve_short_link(
        self,
        authenticated_client: TestClient,
        db_session: Session,
    ) -> None:
        """Resolving a token returns its target identifier and type."""
        letter = LetterFactory.create()
        short_link = ShortLinkFactory.create(
            target_api_id=letter.api_identifier
        )
        db_session.commit()

        response = authenticated_client.get(
            f"/links/short-link/{short_link.token}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data == {
            "token": short_link.token,
            "target_api_id": letter.api_identifier,
            "target_type": "letter",
        }

    def test_resolve_short_link_not_found(
        self,
        authenticated_client: TestClient,
    ) -> None:
        """An unknown token resolves to a 404."""
        response = authenticated_client.get("/links/short-link/does-not-exist")
        assert response.status_code == 404

    def test_resolve_short_link_unauthenticated(
        self,
        unauthenticated_client: TestClient,
        db_session: Session,
    ) -> None:
        """Resolving a short link requires authentication."""
        short_link = ShortLinkFactory.create()
        db_session.commit()

        response = unauthenticated_client.get(
            f"/links/short-link/{short_link.token}"
        )
        assert response.status_code == 401


class TestDeleteShortLink:
    """Tests for revoking short links."""

    def test_delete_short_link(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ) -> None:
        """A creator can revoke their own short link."""
        short_link = ShortLinkFactory.create(creator=current_user)
        db_session.commit()

        response = authenticated_client.delete(
            f"/links/short-link/{short_link.api_identifier}"
        )
        assert response.status_code == 204
        assert db_session.query(ShortLink).count() == 0

    def test_delete_short_link_not_owner(
        self,
        authenticated_client: TestClient,
        db_session: Session,
    ) -> None:
        """A non-creator cannot revoke someone else's short link."""
        short_link = ShortLinkFactory.create()
        db_session.commit()

        response = authenticated_client.delete(
            f"/links/short-link/{short_link.api_identifier}"
        )
        assert response.status_code == 404
        assert db_session.query(ShortLink).count() == 1

    def test_delete_short_link_not_found(
        self,
        authenticated_client: TestClient,
    ) -> None:
        """Revoking an unknown short link returns a 404."""
        response = authenticated_client.delete(
            "/links/short-link/shl_does-not-exist"
        )
        assert response.status_code == 404
