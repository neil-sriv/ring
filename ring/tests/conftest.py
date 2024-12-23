import logging
from typing import TYPE_CHECKING, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import (
    Session,
    sessionmaker,
)

from ring.fast import app
from ring.sqlalchemy_base import Base, get_db
from ring.tests.factories.base_factory import BaseFactory

# Create a new SQLAlchemy engine instance
engine = create_engine("postgresql://ring:ring@test-db:5432/ring_test")

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def logger() -> Generator[logging.Logger, None, None]:
    logger = logging.getLogger(__name__)
    yield logger


@pytest.fixture(scope="session")
def db_engine(logger: logging.Logger) -> Generator[Engine, None, None]:
    logger.info("Creating test database engine")
    try:
        Base.metadata.create_all(bind=engine)
        yield engine
    finally:
        Base.metadata.drop_all(bind=engine)
        logger.info("Dropped test database engine")


def _patch_factories(logger: logging.Logger, session: Session) -> None:
    for factory in BaseFactory.__subclasses__():
        factory._meta.sqlalchemy_session = session


@pytest.fixture(scope="function")
def db_session(
    db_engine: Engine, logger: logging.Logger
) -> Generator[Session, None, None]:
    logger.info("Creating test database session")
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    _patch_factories(logger, session)

    yield session

    session.close()
    transaction.rollback()
    connection.close()
    logger.info("Closed test database session")


@pytest.fixture(scope="function")
def unauthenticated_client(
    db_session: Session, logger: logging.Logger
) -> Generator[TestClient, None, None]:
    logger.info("Creating test client")

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, base_url="http://testserver/api/v1") as c:
        yield c
    logger.info("Closed test client")
