"""Tests for capability-token preview enrichment."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ring.sharing.crud import share_link as share_link_crud
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.unfurl.enrich import enriched_card_for_share


def _shared_letter(db_session: Session, title: str | None = "Spring Issue"):
    group = GroupFactory.create(name="The Book Club")
    letter = LetterFactory.create(group=group, title=title)
    db_session.commit()
    link = share_link_crud.get_or_create_share_link(
        db_session,
        target_api_id=letter.api_identifier,
        created_by_api_id=group.admin.api_identifier,
    )
    db_session.commit()
    return letter, link


class TestEnrichedCardForShare:
    """Test suite for `enriched_card_for_share`."""

    def test_valid_token_names_the_letter_and_group(
        self, db_session: Session
    ) -> None:
        letter, link = _shared_letter(db_session)

        card = enriched_card_for_share(
            db_session, link.token, f"loops/{letter.api_identifier}"
        )

        assert card is not None
        assert card.title == "Spring Issue"
        assert "The Book Club" in card.description

    def test_untitled_letter_falls_back_to_issue_number(
        self, db_session: Session
    ) -> None:
        letter, link = _shared_letter(db_session, title=None)

        card = enriched_card_for_share(
            db_session, link.token, f"loops/{letter.api_identifier}"
        )

        assert card is not None
        assert card.title == f"Issue #{letter.number}"

    def test_unknown_token_is_generic(self, db_session: Session) -> None:
        letter, _ = _shared_letter(db_session)

        assert (
            enriched_card_for_share(
                db_session, "sh_nope", f"loops/{letter.api_identifier}"
            )
            is None
        )

    def test_token_must_match_the_url_it_decorates(
        self, db_session: Session
    ) -> None:
        """A token for letter A must not enrich letter B's preview."""
        _, link = _shared_letter(db_session)

        card = enriched_card_for_share(
            db_session, link.token, "loops/lttr_some-other-letter"
        )

        assert card is None

    def test_deleted_target_is_generic(self, db_session: Session) -> None:
        letter, link = _shared_letter(db_session)
        path = f"loops/{letter.api_identifier}"
        db_session.delete(letter)
        db_session.commit()

        assert enriched_card_for_share(db_session, link.token, path) is None


class TestUnfurlEndpointWithToken:
    """Test suite for GET /unfurl with a ?s= token."""

    def test_token_enriches_the_card(
        self, unauthenticated_client: TestClient, db_session: Session
    ) -> None:
        letter, link = _shared_letter(db_session)

        response = unauthenticated_client.get(
            f"/unfurl/loops/{letter.api_identifier}",
            params={"s": link.token},
        )

        assert response.status_code == 200
        assert 'content="Spring Issue"' in response.text
        # A tokenized card is cached only briefly so revocation takes effect.
        assert "max-age=300" in response.headers["cache-control"]

    def test_no_token_is_generic(
        self, unauthenticated_client: TestClient, db_session: Session
    ) -> None:
        letter, _ = _shared_letter(db_session)

        response = unauthenticated_client.get(
            f"/unfurl/loops/{letter.api_identifier}"
        )

        assert response.status_code == 200
        assert 'content="Spring Issue"' not in response.text
        assert 'content="A newsletter on Ring"' in response.text

    def test_bad_token_falls_back_without_error(
        self, unauthenticated_client: TestClient, db_session: Session
    ) -> None:
        letter, _ = _shared_letter(db_session)

        response = unauthenticated_client.get(
            f"/unfurl/loops/{letter.api_identifier}",
            params={"s": "sh_bogus"},
        )

        assert response.status_code == 200
        assert 'content="A newsletter on Ring"' in response.text
