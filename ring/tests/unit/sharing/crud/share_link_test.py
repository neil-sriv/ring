"""Tests for share link CRUD."""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from ring.sharing.crud import share_link as share_link_crud
from ring.sharing.models.share_link_model import ShareLink


class TestGenerateShareToken:
    """Test suite for token generation."""

    def test_tokens_are_prefixed_and_unguessable(self) -> None:
        token = share_link_crud.generate_share_token()

        assert token.startswith("sh_")
        # token_urlsafe(32) is ~43 chars; well beyond guessable.
        assert len(token) > 40

    def test_tokens_are_unique(self) -> None:
        tokens = {share_link_crud.generate_share_token() for _ in range(100)}

        assert len(tokens) == 100


class TestAppPathForTarget:
    """Test suite for mapping a resource to its app path."""

    def test_letter_maps_to_loops(self) -> None:
        assert (
            share_link_crud.app_path_for_target("lttr_abc") == "loops/lttr_abc"
        )

    def test_unshareable_type_returns_none(self) -> None:
        assert share_link_crud.app_path_for_target("usr_abc") is None


class TestGetOrCreateShareLink:
    """Test suite for minting share links."""

    def test_creates_a_link_on_first_call(self, db_session: Session) -> None:
        link = share_link_crud.get_or_create_share_link(
            db_session, target_api_id="lttr_abc", created_by_api_id="usr_1"
        )
        db_session.commit()

        assert link.token.startswith("sh_")
        assert link.target_api_id == "lttr_abc"
        assert link.created_by_api_id == "usr_1"

    def test_is_idempotent_per_target(self, db_session: Session) -> None:
        """Re-sharing must not rotate the token and break links in flight."""
        first = share_link_crud.get_or_create_share_link(
            db_session, target_api_id="lttr_abc", created_by_api_id="usr_1"
        )
        db_session.commit()
        second = share_link_crud.get_or_create_share_link(
            db_session, target_api_id="lttr_abc", created_by_api_id="usr_2"
        )
        db_session.commit()

        assert first.token == second.token
        assert (
            db_session.query(ShareLink)
            .filter(ShareLink.target_api_id == "lttr_abc")
            .count()
            == 1
        )

    def test_recovers_from_concurrent_insert(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A unique-constraint race re-fetches the winning row instead of 500."""
        existing = share_link_crud.get_or_create_share_link(
            db_session, target_api_id="lttr_abc", created_by_api_id="usr_1"
        )
        db_session.commit()

        lookups = {"count": 0}
        original = share_link_crud.get_share_link_for_target

        def miss_then_hit(db: Session, target_api_id: str) -> ShareLink | None:
            lookups["count"] += 1
            if lookups["count"] == 1:
                return None
            return original(db, target_api_id)

        monkeypatch.setattr(
            share_link_crud, "get_share_link_for_target", miss_then_hit
        )

        recovered = share_link_crud.get_or_create_share_link(
            db_session, target_api_id="lttr_abc", created_by_api_id="usr_2"
        )
        db_session.commit()

        assert recovered.id == existing.id
        assert recovered.token == existing.token


class TestLookupAndRevoke:
    """Test suite for looking up and revoking share links."""

    def test_get_by_token(self, db_session: Session) -> None:
        link = share_link_crud.get_or_create_share_link(
            db_session, target_api_id="lttr_abc", created_by_api_id="usr_1"
        )
        db_session.commit()

        assert (
            share_link_crud.get_share_link_by_token(db_session, link.token)
            == link
        )

    def test_get_by_unknown_token_is_none(self, db_session: Session) -> None:
        assert (
            share_link_crud.get_share_link_by_token(db_session, "sh_nope")
            is None
        )

    def test_revoke_hard_deletes(self, db_session: Session) -> None:
        link = share_link_crud.get_or_create_share_link(
            db_session, target_api_id="lttr_abc", created_by_api_id="usr_1"
        )
        db_session.commit()

        share_link_crud.revoke_share_link(db_session, link)
        db_session.commit()

        assert (
            share_link_crud.get_share_link_by_token(db_session, link.token)
            is None
        )
