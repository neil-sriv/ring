from sqlalchemy import select

from ring.parties.models.user_model import User
from ring.scripts.script_base import script_di
from ring.sqlalchemy_base import Session


@script_di()
def run_script(db: Session) -> None:
    users = db.scalars(select(User)).all()
    print(users)
