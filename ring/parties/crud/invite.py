from __future__ import annotations
from secrets import token_urlsafe
from typing import TYPE_CHECKING, Sequence
from ring.api_identifier import util as api_identifier_crud
from ring.email_util import CHARSET, EmailDraft, send_email
from ring.parties.models.group_model import Group
from ring.parties.models.invite_model import Invite
from ring.parties.models.user_model import User
from sqlalchemy import select

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
        select(Invite).filter(
            Invite.email == email,
            Invite.is_expired.is_(expired),
        )
    )


def get_invite_by_token(
    db: Session, token: str, expired: bool = False
) -> Invite | None:
    return db.scalar(
        select(Invite).filter(
            Invite._deprecated_token == token,
            Invite.is_expired.is_(expired),
        )
    )


def invite_users(
    db: Session, group: Group, inviter: User, emails: Sequence[str]
) -> list[Invite]:
    invites: list[Invite] = []
    for email in emails:
        existing_invite = get_invite_by_email(db, email)
        if existing_invite:
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
    # generate token
    token = token_urlsafe(32)
    db_invite = Invite.create(email, token, inviter, group)
    db.add(db_invite)
    return db_invite


@register_task_factory(name="email_user_invites")
def email_user_invites(self: CeleryTask, invite_ids: list[int]) -> None:
    invites = self.session.scalars(
        select(Invite).filter(Invite.id.in_(invite_ids))
    ).all()
    email_drafts = [
        construct_invite_email(i.email, i.group, i.token) for i in invites
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
