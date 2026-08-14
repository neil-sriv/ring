"""Tests for the app links embedded in outbound email.

Emailed links have to stay on the origin the frontend is served from. The
frontend build bakes in an absolute `VITE_API_URL`, so a link on a different
scheme lands the recipient on an origin where every API call is cross-origin
and the CORS preflight is rejected - an `http://` reset link is what broke
password resets in production.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from ring.email_util import EmailDraft
from ring.letters.constants import LetterStatus
from ring.lib.app_links import app_url
from ring.parties.crud.authn import construct_password_reset_email
from ring.parties.crud.invite import construct_invite_email
from ring.tasks.crud.reminder_email_task import construct_reminder_email
from ring.tasks.crud.response_open_email_task import (
    construct_response_open_email,
)
from ring.tasks.crud.send_email_task import construct_send_letter_email
from ring.tasks.crud.waiting_response_email_task import (
    construct_waiting_response_email,
)
from ring.tests.factories.parties.group_factory import GroupFactory


def _bodies(draft: EmailDraft) -> list[str]:
    return [part["Data"] for part in draft.message["Body"].values()]


class TestAppUrl:
    """Test suite for building absolute links into the web app."""

    def test_builds_an_https_url_for_a_path(self) -> None:
        url = app_url("loops/lttr_abc123")

        assert url.startswith("https://")
        assert url.endswith("/loops/lttr_abc123")

    def test_leading_slash_does_not_double_up(self) -> None:
        assert app_url("/loops/lttr_abc123") == app_url("loops/lttr_abc123")


class TestOutboundEmailLinks:
    """Every email that links into the app must link to it over https."""

    def test_emails_link_to_the_app_over_https(
        self, db_session: Session
    ) -> None:
        group = GroupFactory.create()
        db_session.commit()
        letter_api_id = "lttr_abc123"
        letter_url = app_url(f"loops/{letter_api_id}")

        drafts_and_links: list[tuple[EmailDraft, str]] = [
            (
                construct_password_reset_email(
                    "user@example.com", "reset-token"
                ),
                app_url("reset-password/reset-token"),
            ),
            (
                construct_invite_email(
                    "user@example.com", group, "invite-token"
                ),
                app_url("register/invite-token"),
            ),
            (
                construct_send_letter_email(
                    ["user@example.com"],
                    "Ring Newsletter #1",
                    letter_api_id,
                    {"Favorite memory?": [("Dana: A good one", [])]},
                ),
                letter_url,
            ),
            (
                construct_response_open_email(
                    ["user@example.com"], group.name, letter_api_id, "#1"
                ),
                letter_url,
            ),
            (
                construct_reminder_email(
                    ["user@example.com"],
                    group.name,
                    letter_api_id,
                    LetterStatus.IN_PROGRESS,
                ),
                letter_url,
            ),
            (
                construct_waiting_response_email(
                    ["user@example.com"],
                    group.name,
                    letter_api_id,
                    "#1",
                ),
                letter_url,
            ),
        ]

        insecure_base = app_url("").replace("https://", "http://", 1)
        for draft, expected_link in drafts_and_links:
            bodies = _bodies(draft)
            assert any(expected_link in body for body in bodies), expected_link
            for body in bodies:
                assert insecure_base not in body, expected_link
