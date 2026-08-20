"""Preview copy for the app paths people paste into chat.

Slack, Discord, and iMessage build a preview from the Open Graph tags in the
first HTML response for a URL and never run JavaScript, so the SPA shell
(`react/index.html`) is all they can see today. Per-path copy has to come from
the server instead.

Everything here is static, public copy. A preview renders for everyone who can
see the channel the link was pasted into, not just the recipient who is able
to sign in, so a card never names a group, letter, or person.
"""

from __future__ import annotations

from dataclasses import dataclass

SITE_NAME = "Ring"
OG_IMAGE_PATH = "assets/images/og-card.png"
OG_IMAGE_WIDTH = 1200
OG_IMAGE_HEIGHT = 630
OG_IMAGE_ALT = "The Ring logo on a dark background"


@dataclass(frozen=True)
class UnfurlCard:
    """Title and description a chat client renders for a shared link."""

    title: str
    description: str


SITE_CARD = UnfurlCard(
    title="Ring",
    description=(
        "Ring asks your group the same few questions on a cadence, then "
        "collects everyone's answers into one newsletter."
    ),
)

# Longest-matching path prefix wins, so order is by specificity.
_CARDS_BY_PREFIX: tuple[tuple[str, UnfurlCard], ...] = (
    (
        "loops",
        UnfurlCard(
            title="A newsletter on Ring",
            description=(
                "Sign in to read this newsletter and everyone else's answers."
            ),
        ),
    ),
    (
        "register",
        UnfurlCard(
            title="Your invitation to Ring",
            description=(
                "Open this invitation to join the group and answer its first "
                "questions."
            ),
        ),
    ),
    (
        "documents",
        UnfurlCard(
            title="A notebook on Ring",
            description="Sign in to write in this notebook with your group.",
        ),
    ),
    (
        "groups",
        UnfurlCard(
            title="A group on Ring",
            description=(
                "Sign in to see this group's questions, answers, and "
                "newsletters."
            ),
        ),
    ),
)


def card_for_path(path: str) -> UnfurlCard:
    """Pick the preview copy for a path within the web app.

    Args:
        path (str): Path the link pointed at, with or without a leading slash
            (e.g. `/loops/lttr_abc123`)

    Returns:
        UnfurlCard: Copy for that path, falling back to the site-wide card for
            anything unrecognized
    """
    normalized = path.strip("/").casefold()
    for prefix, card in _CARDS_BY_PREFIX:
        if normalized == prefix or normalized.startswith(f"{prefix}/"):
            return card
    return SITE_CARD
