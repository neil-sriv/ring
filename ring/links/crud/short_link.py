"""CRUD operations for short links.

Pure functions that operate on a SQLAlchemy ``Session`` and return ORM
instances. Creation is idempotent per ``(target_api_id, creator)``; a unique
constraint plus ``IntegrityError`` handling covers concurrent inserts. Token
generation retries on the (unlikely) event of a collision with the unique
``token`` column.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ring.links.models.short_link_model import ShortLink, generate_token
from ring.parties.models.user_model import User

# Bounded retries to avoid an unbounded loop if the RNG or DB misbehaves. With an
# 8-char base62 token the collision probability is negligible in practice.
_MAX_TOKEN_ATTEMPTS = 8


def get_short_link_by_token(db: Session, token: str) -> ShortLink | None:
    """Look up a short link by its token.

    Args:
        db (Session): Database session.
        token (str): The short link token.

    Returns:
        ShortLink | None: The matching short link, or ``None``.
    """
    return db.scalars(
        select(ShortLink).where(ShortLink.token == token)
    ).one_or_none()


def get_short_link_for_target(
    db: Session, target_api_id: str, creator: User
) -> ShortLink | None:
    """Find an existing short link created by ``creator`` for a target.

    Args:
        db (Session): Database session.
        target_api_id (str): API identifier of the shared resource.
        creator (User): The user who created the link.

    Returns:
        ShortLink | None: The existing short link, or ``None``.
    """
    return db.scalars(
        select(ShortLink)
        .where(ShortLink.target_api_id == target_api_id)
        .where(ShortLink.creator_id == creator.id)
    ).one_or_none()


def create_short_link(
    db: Session, target_api_id: str, creator: User
) -> ShortLink:
    """Create a short link, reusing an existing one for the same target/creator.

    Creation is idempotent per ``(target_api_id, creator)``. The unique
    constraint ``uq_short_link_target_creator`` is the source of truth: a
    concurrent create that loses the race is recovered via ``IntegrityError``
    and a re-fetch of the winning row (and a token collision retries).

    Args:
        db (Session): Database session.
        target_api_id (str): API identifier of the resource to share.
        creator (User): User creating the link.

    Returns:
        ShortLink: The new or pre-existing short link.
    """
    existing = get_short_link_for_target(db, target_api_id, creator)
    if existing is not None:
        return existing

    for _ in range(_MAX_TOKEN_ATTEMPTS):
        token = _generate_unique_token(db)
        short_link = ShortLink.create(
            target_api_id=target_api_id, creator=creator, token=token
        )
        db.add(short_link)
        try:
            with db.begin_nested():
                db.flush()
        except IntegrityError:
            db.expunge(short_link)
            winner = get_short_link_for_target(db, target_api_id, creator)
            if winner is not None:
                return winner
            continue
        return short_link

    winner = get_short_link_for_target(db, target_api_id, creator)
    if winner is not None:
        return winner
    raise RuntimeError("Could not create a unique short link")


def delete_short_link(db: Session, short_link: ShortLink) -> None:
    """Hard-delete a short link (revocation).

    Args:
        db (Session): Database session.
        short_link (ShortLink): The short link to delete.
    """
    db.delete(short_link)


def _generate_unique_token(db: Session) -> str:
    """Generate a token not already present in the database.

    Args:
        db (Session): Database session.

    Returns:
        str: A token unique within the ``short_link`` table.

    Raises:
        RuntimeError: If a unique token could not be generated after several
            attempts.
    """
    for _ in range(_MAX_TOKEN_ATTEMPTS):
        token = generate_token()
        if get_short_link_by_token(db, token) is None:
            return token
    raise RuntimeError("Could not generate a unique short link token")
