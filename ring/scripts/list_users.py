from sqlalchemy import select
from ring.postgres_models.user_model import User
from ring.sqlalchemy_base import Session
from ring.scripts.script_base import script


@script
def run_script(db: Session) -> None:
    users = db.scalars(select(User)).all()
    print(users)
