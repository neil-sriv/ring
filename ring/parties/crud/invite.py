from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from sqlalchemy import select

from ring.api_identifier import util as api_identifier_crud
from ring.email_util import CHARSET, EmailDraft, send_email
from ring.parties.crud.one_time_token import generate_token, validate_token
from ring.parties.crud.user import get_user_by_email
from ring.parties.models.group_model import Group
from ring.parties.models.invite_model import Invite
from ring.parties.models.one_time_token_model import OneTimeToken, TokenType
from ring.parties.models.user_model import User
from ring.worker.celery_app import CeleryTask, register_task_factory

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

    :param db: Database session
    :type db: Session
    :param inviter_api_id: API identifier of the inviter
    :type inviter_api_id: str
    :param expired: Whether to get expired invites, defaults to False
    :type expired: bool, optional
    :param skip: Number of records to skip, defaults to 0
    :type skip: int, optional
    :param limit: Maximum number of records to return, defaults to 100
    :type limit: int, optional
    :return: List of invites
    :rtype: Sequence[Invite]
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

    :param db: Database session
    :type db: Session
    :param email: Email address to look up
    :type email: str
    :param expired: Whether to include expired invites, defaults to False
    :type expired: bool, optional
    :return: Found invite or None
    :rtype: Invite | None
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

    :param db: Database session
    :type db: Session
    :param token: Token string to look up
    :type token: str
    :return: Found invite or None
    :rtype: Invite | None
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

    :param db: Database session
    :type db: Session
    :param group: Group to invite users to
    :type group: Group
    :param inviter: User sending the invites
    :type inviter: User
    :param emails: Email addresses to invite
    :type emails: Sequence[str]
    :return: List of created invites (excludes existing users/invites)
    :rtype: list[Invite]
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

    :param db: Database session
    :type db: Session
    :param email: Email address to invite
    :type email: str
    :param inviter: User sending the invite
    :type inviter: User
    :param group: Group to invite to
    :type group: Group
    :return: Created invite
    :rtype: Invite
    """
    # generate token
    one_time_token = generate_token(TokenType.INVITE, email, token=None)
    db_invite = Invite.create(email, one_time_token, inviter, group)
    db.add(db_invite)
    return db_invite


@register_task_factory(name="email_user_invites")
def email_user_invites(self: CeleryTask, invite_ids: list[int]) -> None:
    """Send invitation emails to users.

    :param self: Celery task instance
    :type self: CeleryTask
    :param invite_ids: List of invite IDs to send emails for
    :type invite_ids: list[int]
    """
    invites = self.session.scalars(
        select(Invite).filter(Invite.id.in_(invite_ids))
    ).all()
    email_drafts = [
        construct_invite_email(i.email, i.group, i.one_time_token.token)
        for i in invites
    ]
    for draft in email_drafts:
        send_email(draft)
    self.session.commit()
    return None


def construct_invite_email(
    recipient: str,
    group: Group,
    token: str,
) -> EmailDraft:
    """Construct an email draft for a group invitation.

    :param recipient: Email address to send to
    :type recipient: str
    :param group: Group being invited to
    :type group: Group
    :param token: One-time token for registration
    :type token: str
    :return: Email draft ready to send
    :rtype: EmailDraft
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
