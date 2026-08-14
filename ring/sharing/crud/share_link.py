"""CRUD for capability share links."""

from __future__ import annotations

import secrets
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from ring.api_identifier.api_identified_model import APIPrefix
from ring.sharing.models.share_link_model import ShareLink

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

# Prefixed so the value is recognizable in logs/URLs; 32 url-safe bytes is 256
# bits of entropy, which makes the token unguessable and enumeration-proof.
SHARE_TOKEN_PREFIX = "sh"
_SHARE_TOKEN_BYTES = 32
_MAX_CREATE_ATTEMPTS = 8

# Which app path a resource lives at, keyed by API-id prefix. Also the set of
# resources a preview can be enriched for.
_APP_PATH_BY_PREFIX: dict[str, str] = {
    APIPrefix.LETTER.value: "loops",
    APIPrefix.DOCUMENT.value: "documents",
    APIPrefix.GROUP.value: "groups",
}


def generate_share_token() -> str:
    """Mint a new capability token.

    Returns:
        str: A prefixed, url-safe, 256-bit random token
    """
    return f"{SHARE_TOKEN_PREFIX}_{secrets.token_urlsafe(_SHARE_TOKEN_BYTES)}"


def app_path_for_target(target_api_id: str) -> str | None:
    """Map a resource's API id to the app path a person would open.

    Args:
        target_api_id (str): API id such as `lttr_...`

    Returns:
        str | None: Path like `loops/lttr_...`, or None if the resource type is
            not shareable
    """
    prefix = target_api_id.split("_", 1)[0]
    base = _APP_PATH_BY_PREFIX.get(prefix)
    if base is None:
        return None
    return f"{base}/{target_api_id}"


def get_share_link_by_token(db: Session, token: str) -> ShareLink | None:
    """Look up a share link by its capability token.

    Args:
        db (Session): Database session
        token (str): The token from the shared URL

    Returns:
        ShareLink | None: The link, or None if the token is unknown
    """
    return db.scalar(select(ShareLink).where(ShareLink.token == token))


def get_share_link_for_target(
    db: Session, target_api_id: str
) -> ShareLink | None:
    """Return the existing share link for a resource, if one was minted.

    Args:
        db (Session): Database session
        target_api_id (str): API id of the shared resource

    Returns:
        ShareLink | None: The link, or None if the resource has no link yet
    """
    return db.scalar(
        select(ShareLink).where(ShareLink.target_api_id == target_api_id)
    )


def get_or_create_share_link(
    db: Session, target_api_id: str, created_by_api_id: str
) -> ShareLink:
    """Return the resource's share link, minting one on first use.

    Idempotent so a resource has one stable link: re-sharing does not rotate
    the token and invalidate links already in flight. Uniqueness of
    ``target_api_id`` is enforced in the database; a concurrent mint that
    loses the race is recovered via ``IntegrityError`` and a re-fetch.

    Args:
        db (Session): Database session
        target_api_id (str): API id of the resource to share
        created_by_api_id (str): API id of the member minting the link

    Returns:
        ShareLink: The existing or newly created link
    """
    existing = get_share_link_for_target(db, target_api_id)
    if existing is not None:
        return existing

    for _ in range(_MAX_CREATE_ATTEMPTS):
        share_link = ShareLink.create(
            token=generate_share_token(),
            target_api_id=target_api_id,
            created_by_api_id=created_by_api_id,
        )
        db.add(share_link)
        try:
            with db.begin_nested():
                db.flush()
        except IntegrityError:
            db.expunge(share_link)
            winner = get_share_link_for_target(db, target_api_id)
            if winner is not None:
                return winner
            continue
        return share_link

    winner = get_share_link_for_target(db, target_api_id)
    if winner is not None:
        return winner
    raise RuntimeError("Could not create a unique share link")


def revoke_share_link(db: Session, share_link: ShareLink) -> None:
    """Delete a share link so its URL stops enriching previews.

    Hard delete per the project convention; revocation should leave nothing
    behind that could still resolve the token.

    Args:
        db (Session): Database session
        share_link (ShareLink): The link to revoke
    """
    db.delete(share_link)
