"""CRUD operations for managing group invitations.

This module provides functions for creating and managing invitations to join groups,
including email notifications and token validation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from sqlalchemy import select

from ring.api_identifier import util as api_identifier_crud
from ring.apscheduler.scheduler import job_factory
from ring.email_util import CHARSET, EmailDraft, send_email
from ring.parties.crud.one_time_token import generate_token, validate_token
from ring.parties.crud.user import get_user_by_email
from ring.parties.models.group_model import Group
from ring.parties.models.invite_model import Invite
from ring.parties.models.one_time_token_model import OneTimeToken, TokenType
from ring.parties.models.user_model import User

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_invites(
    db: Session,
    inviter_api_id: str,
    expired: bool = False,
    skip: int = 0,
    limit: int = 100,
) -> Sequence[Invite]:
    """Get all invites sent by a user.

    Args:
        db (Session): Database session
        inviter_api_id (str): API identifier of the inviter
        expired (bool, optional): Whether to get expired invites. Defaults to False.
        skip (int, optional): Number of records to skip. Defaults to 0.
        limit (int, optional): Maximum number of records to return. Defaults to 100.

    Returns:
        Sequence[Invite]: List of invites
    """
    inviter = api_identifier_crud.get_model(db, User, api_id=inviter_api_id)
    return db.scalars(
        select(Invite)
        .join(Invite.one_time_token)
        .filter(
            Invite.inviter == inviter,
            OneTimeToken.is_expired.is_(expired),  # type: ignore
        )
        .offset(skip)
        .limit(limit)
    ).all()


def get_invite_by_email(
    db: Session, email: str, expired: bool = False
) -> Invite | None:
    """Get an invite by email address.

    Args:
        db (Session): Database session
        email (str): Email address to look up
        expired (bool, optional): Whether to include expired invites. Defaults to False.

    Returns:
        Invite | None: Found invite or None
    """
    return db.scalar(
        select(Invite)
        .join(Invite.one_time_token)
        .filter(
            Invite.email == email,
            OneTimeToken.is_expired.is_(expired),  # type: ignore
        )
    )


def get_invite_by_token(db: Session, token: str) -> Invite | None:
    """Get an invite by its token string.

    Args:
        db (Session): Database session
        token (str): Token string to look up

    Returns:
        Invite | None: Found invite or None
    """
    invite = db.scalar(
        select(Invite)
        .join(Invite.one_time_token)
        .filter(
            OneTimeToken.token == token,
            OneTimeToken.type == TokenType.INVITE,
        )
    )
    if not invite:
        return None
    validate_token(db, invite.one_time_token)
    return invite


def invite_users(
    db: Session, group: Group, inviter: User, emails: Sequence[str]
) -> list[Invite]:
    """Invite multiple users to a group.

    Args:
        db (Session): Database session
        group (Group): Group to invite users to
        inviter (User): User sending the invites
        emails (Sequence[str]): Email addresses to invite

    Returns:
        list[Invite]: List of created invites (excludes existing users/invites)
    """
    invites: list[Invite] = []
    for email in emails:
        existing_invite = get_invite_by_email(db, email)
        existing_user = get_user_by_email(db, email)
        if existing_invite or existing_user:
            continue
        invite = create_invite(db, email, inviter, group)
        invites.append(invite)
    return invites


def create_invite(
    db: Session,
    email: str,
    inviter: User,
    group: Group,
) -> Invite:
    """Create a new invite.

    Args:
        db (Session): Database session
        email (str): Email address to invite
        inviter (User): User sending the invite
        group (Group): Group to invite to

    Returns:
        Invite: Created invite
    """
    one_time_token = generate_token(TokenType.INVITE, email, token=None)
    db_invite = Invite.create(email, one_time_token, inviter, group)
    db.add(db_invite)
    return db_invite


@job_factory("email_user_invites")
def email_user_invites(db: Session, invite_ids: list[int]) -> None:
    """Send invitation emails to users.

    Args:
        db (Session): Database session
        invite_ids (list[int]): List of invite IDs to send emails for
    """
    invites = db.scalars(
        select(Invite).filter(Invite.id.in_(invite_ids))
    ).all()
    email_drafts = [
        construct_invite_email(i.email, i.group, i.one_time_token.token)
        for i in invites
    ]
    for draft in email_drafts:
        send_email(draft)
    db.commit()
    return None


def construct_invite_email(
    recipient: str,
    group: Group,
    token: str,
) -> EmailDraft:
    """Construct an email draft for a group invitation.

    Args:
        recipient (str): Email address to send to
        group (Group): Group being invited to
        token (str): One-time token for registration

    Returns:
        EmailDraft: Email draft ready to send
    """
    BODY_HTML = """
    <html>
    <head></head>
    <body>
    <h1 style="text-align:center">Join <b>{group_name}</b> and make custom monthly newsletters with your friends!</h1>
    <spacer type="" size="">
    <span>Click the link below to join the group and start creating newsletters!</span>
    <spacer type="" size="">
    <h3>Please use this custom URL to create an account: <a href="http://ring.neilsriv.tech/register/{token}">http://ring.neilsriv.tech/register/{token}</a></h2>
    <p>
    You've been invited to join a Ring Newsletter! Ring is a custom newsletter platform made by Neil Srivastava that allows you to create newsletters with your friends.
    </p>
    </body>
    </html>
                """.format(group_name=group.name, token=token)
    return EmailDraft(
        destination={"ToAddresses": [recipient]},
        message={
            "Subject": {
                "Data": "You've been invited to join a Ring Newsletter!",
                "Charset": CHARSET,
            },
            "Body": {
                "Html": {
                    "Data": BODY_HTML,
                    "Charset": CHARSET,
                },
            },
        },
    )
