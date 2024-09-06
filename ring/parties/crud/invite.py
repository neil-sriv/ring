
from __future__ import annotations
from secrets import token_urlsafe
from datetime import datetime
from typing import TYPE_CHECKING, Sequence
from ring.api_identifier import util as api_identifier_crud
from ring.parties.models.invite_model import Invite
from ring.parties.models.user_model import User
from sqlalchemy import select

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_invites(
    db: Session, inviter_api_id: str, expired: bool = False, skip: int = 0, limit: int = 100
) -> Sequence[Invite]:
    inviter = api_identifier_crud.get_model(db, User, api_id=inviter_api_id)
    return db.scalars(
        select(Invite)
        .filter(
            Invite.inviter == inviter,
            Invite.is_expired.is_(expired),
        )
        .offset(skip)
        .limit(limit)
    ).all()


def get_invite_by_email(
    db: Session, email: str, expired: bool = False
) -> Invite | None:
    return db.scalar(
        select(Invite)
        .filter(
            Invite.email == email,
            Invite.is_expired.is_(expired),
        )
    )

def get_invite_by_token(
    db: Session, token: str, expired: bool = False
    ) -> Invite | None:
        return db.scalar(
            select(Invite)
            .filter(
                Invite.token == token,
                Invite.is_expired.is_(expired),
            )
        )


def create_invite(db: Session, email: str, inviter_api_id: str, ) -> Invite:
    inviter = api_identifier_crud.get_model(
        db,
        User,
        api_id=inviter_api_id,
    )
    # generate token
    token = token_urlsafe(16)
    db_invite = Invite.create(email, token, inviter)
    db.add(db_invite)
    return db_invite
