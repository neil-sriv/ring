from sqlalchemy.orm import Session

from ring.parties.crud import user


def test_get_users(db_session: Session):
    users = user.get_users(db_session)

    assert len(users) == 0
