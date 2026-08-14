"""Turn a capability token into richer, still-safe preview copy.

A shared URL can carry a `?s=<token>` capability minted by
`ring/sharing/`. When it does, the preview can name the actual resource
(newsletter title, group, response count) instead of the generic card. Only a
minimal, public-safe subset is ever disclosed - never the resource's contents -
so a leaked link exposes little, and revoking the token drops the card back to
generic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from ring.api_identifier.api_identified_model import APIPrefix
from ring.api_identifier.util import IDNotFoundException, bulk_get_models
from ring.letters.models.letter_model import Letter
from ring.sharing.crud import share_link as share_link_crud
from ring.unfurl.cards import UnfurlCard

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def _path_segments(path: str) -> list[str]:
    return [segment for segment in path.strip("/").split("/") if segment]


def _letter_card(letter: Letter) -> UnfurlCard:
    """Public-safe copy for a letter: title, group, and how many replied."""
    if letter.title:
        title = letter.title
    elif letter.number is not None:
        title = f"Issue #{letter.number}"
    else:
        title = "A newsletter on Ring"

    group_name = letter.group.name if letter.group else "a group"
    responder_count = len(letter.responders)
    replies = "reply" if responder_count == 1 else "replies"
    description = (
        f"{group_name} · {responder_count} {replies}. Sign in to read."
    )

    return UnfurlCard(title=title, description=description)


def enriched_card_for_share(
    db: Session, token: str, path: str
) -> UnfurlCard | None:
    """Resolve a capability token into enriched preview copy.

    Args:
        db (Session): Database session
        token (str): The `?s=` token from the shared URL
        path (str): The app path the link pointed at, used to bind the token to
            the URL it decorates

    Returns:
        UnfurlCard | None: Enriched copy, or None to fall back to the generic
            card (unknown/mismatched token, deleted resource, or a resource
            type without a rich card)
    """
    share_link = share_link_crud.get_share_link_by_token(db, token)
    if share_link is None:
        return None

    # Bind the token to the URL it is decorating: a token for one resource must
    # not enrich the preview of a different resource's link.
    if share_link.target_api_id not in _path_segments(path):
        return None

    try:
        [target] = bulk_get_models(db, [share_link.target_api_id])
    except (IDNotFoundException, ValueError):
        # Resource was deleted after the link was minted.
        return None

    prefix = share_link.target_api_id.split("_", 1)[0]
    if prefix == APIPrefix.LETTER.value and isinstance(target, Letter):
        return _letter_card(target)

    # Other resource types get the generic card until they grow a safe one.
    logger.debug("No enriched card for share target {}", prefix)
    return None
