from sqlalchemy.orm import Session

from ring.parties.crud import user as user_crud
from ring.tests.factories.parties.user_factory import UserFactory


def test_get_users(db_session: Session):
    users = user_crud.get_users(db_session)

    assert len(users) == 0

    test = [UserFactory.create() for _ in range(10)]
    assert len(test) == 10
    db_session.commit()

    users = user_crud.get_users(db_session)
    assert len(users) == 10
