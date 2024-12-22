import logging
from pprint import pformat

from sqlalchemy.orm import Session

from ring.parties.crud import user


def test_get_users(logger: logging.Logger, db_session: Session):
    users = user.get_users(db_session)

    logger.warning(pformat(db_session.get_bind().__dict__))

    assert len(users) == 0
