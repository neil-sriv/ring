from ring.scripts.script_base import script_di
from sqlalchemy.orm import Session
from sqlalchemy import select
from ring.parties.models.invite_model import Invite
from ring.parties.models.one_time_token_model import OneTimeToken


@script_di()
def run_script(db: Session) -> None:
    invites = db.scalars(select(Invite)).all()
    for invite in invites:
        if invite._deprecated_token is None:
            continue
        ott = OneTimeToken.create(invite._deprecated_token)  # type: ignore
        db.add(ott)
        invite.one_time_token = ott
        invite.one_time_token.ttl = 0
        invite.one_time_token.used = True
    db.commit()
