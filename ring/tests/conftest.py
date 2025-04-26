"""Test configuration and fixtures for Ring's test suite.

This module provides core test fixtures for database sessions, logging,
and HTTP clients. It sets up the test environment and manages test resources.
"""

from __future__ import annotations

import logging
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import (
    Session,
    sessionmaker,
)

from ring.fastapp.config import get_config
from ring.fastapp.fast import app
from ring.sqlalchemy_base import Base, get_db
from ring.tests.factories.base_factory import ALL_FACTORIES, BaseFactory

# Create a new SQLAlchemy engine instance
# engine = create_engine("postgresql://ring:ring@test-db:5432/ring_test")
config = get_config()
engine = create_engine(config.cockroach_database_uri)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def logger() -> Generator[logging.Logger, None, None]:
    """Create a logger instance for test output.

    This fixture provides a logger that can be used throughout the test suite
    to track test execution and debugging information.

    Yields:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(__name__)
    yield logger


@pytest.fixture(scope="session")
def db_engine(logger: logging.Logger) -> Generator[Engine, None, None]:
    """Create and manage the test database engine.

    This fixture creates a fresh database engine for testing, creates all tables,
    and ensures proper cleanup after tests.

    Args:
        logger (logging.Logger): Logger instance for tracking database operations

    Yields:
        Engine: SQLAlchemy engine instance for test database
    """
    logger.info("Creating test database engine")
    try:
        Base.metadata.create_all(bind=engine)
        yield engine
    finally:
        Base.metadata.drop_all(bind=engine)
        logger.info("Dropped test database engine")


def _patch_factories(logger: logging.Logger, session: Session) -> None:
    """Initialize and patch test factories with the current database session.

    This helper function ensures all test factories are properly configured
    with the current database session for test data creation.

    Args:
        logger (logging.Logger): Logger instance for tracking factory operations
        session (Session): Current database session
    """
    from ring.tests.factories.entrypoint.initialize import initialize_factories

    initialize_factories()

    for factory in ALL_FACTORIES:
        factory._meta.sqlalchemy_session = session


@pytest.fixture(scope="function")
def db_session(
    db_engine: Engine, logger: logging.Logger
) -> Generator[Session, None, None]:
    """Create a database session for each test function.

    This fixture provides a fresh database session for each test, wrapped in
    a transaction that is rolled back after the test completes.

    Args:
        db_engine (Engine): Test database engine
        logger (logging.Logger): Logger instance for tracking session operations

    Yields:
        Session: SQLAlchemy session instance for test database
    """
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
    """Create a test client without authentication.

    This fixture provides a FastAPI TestClient instance configured with the
    test database session but without any authentication.

    Args:
        db_session (Session): Test database session
        logger (logging.Logger): Logger instance for tracking client operations

    Yields:
        TestClient: FastAPI test client instance
    """
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
