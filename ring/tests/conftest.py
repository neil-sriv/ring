import logging
import sys
from typing import TYPE_CHECKING, Generator

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import (
    Session,
    sessionmaker,
)

from ring.config import RingConfig
from ring.fast import app

# from ring.sqlalchemy_base import Base, get_db


if TYPE_CHECKING:
    from ring.sqlalchemy_base import get_db


load_dotenv()


class TestConfig(RingConfig):
    sqlalchemy_database_uri: str = (
        "postgresql://ring:ring@test-db:5432/ring_test"
    )


# Set up a test database URL
TEST_SQLALCHEMY_DATABASE_URL = TestConfig().sqlalchemy_database_uri  # type: ignore

# Create a new SQLAlchemy engine instance
engine = create_engine(TEST_SQLALCHEMY_DATABASE_URL)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def logger() -> Generator[logging.Logger, None, None]:
    logger = logging.getLogger(__name__)
    yield logger


@pytest.fixture(scope="session")
def setup_db(
    logger: logging.Logger, db_engine: Engine
) -> Generator[None, None, None]:
    logger.info("Creating test database")
    # Base.metadata.create_all(bind=db_engine)
    yield
    logger.info("Dropping test database")
    # Base.metadata.drop_all(bind=db_engine)


@pytest.fixture(scope="session")
def db_engine(logger: logging.Logger) -> Generator[Engine, None, None]:
    logger.info("Creating test database engine")
    try:
        # Base.metadata.create_all(bind=engine)
        yield engine
    finally:
        # Base.metadata.drop_all(bind=engine)
        logger.info("Dropped test database engine")


@pytest.fixture(scope="session")
def db_session(
    db_engine: Engine, logger: logging.Logger
) -> Generator[Session, None, None]:
    logger.info("Creating test database session")
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()
    logger.info("Closed test database session")


@pytest.fixture(scope="function")
def client(
    db_session: Session, logger: logging.Logger
) -> Generator[TestClient, None, None]:
    logger.info("Creating test client")

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    logger.info("Closed test client")
