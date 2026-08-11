"""Test configuration and fixtures for Ring's test suite.

This module provides core test fixtures for database sessions, logging,
and HTTP clients. It sets up the test environment and manages test resources.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Generator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import (
    Session,
    sessionmaker,
)

from ring.fastapp.config import get_config
from ring.fastapp.fast import app
from ring.search.crud.hybrid_search import _generate_text_embedding
from ring.sqlalchemy_base import Base, get_db
from ring.tests.factories.base_factory import ALL_FACTORIES, BaseFactory

# Create a new SQLAlchemy engine instance
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


def _execute_schema_file(engine: Engine, logger: logging.Logger) -> None:
    """Execute the schema.sql file to create the database schema.

    Args:
        engine (Engine): SQLAlchemy engine instance
        logger (logging.Logger): Logger instance for tracking operations
    """
    schema_path = Path(__file__).parent.parent / "db" / "schema.sql"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found at {schema_path}")

    logger.info(f"Reading schema from {schema_path}")
    with open(schema_path) as f:
        schema_sql = f.read()

    # Split the SQL file into individual statements
    # This is a simple split that works for most cases, but might need adjustment
    # for more complex SQL files with semicolons in string literals
    statements = [
        stmt.strip() for stmt in schema_sql.split(";") if stmt.strip()
    ]

    with engine.connect() as conn:
        for statement in statements:
            if statement:  # Skip empty statements
                logger.debug(f"Executing: {statement[:100]}...")
                conn.execute(text(statement))
        conn.commit()


def _drop_all_objects(engine: Engine, logger: logging.Logger) -> None:
    """Drop all existing tables and sequences from the database.

    Args:
        engine (Engine): SQLAlchemy engine instance
        logger (logging.Logger): Logger instance for tracking operations
    """
    with engine.connect() as conn:
        # Drop all tables first (this will also drop dependent sequences)
        result = conn.execute(
            text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        )
        tables = [row[0] for row in result]

        for table in tables:
            conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))

        # Drop any remaining sequences
        result = conn.execute(
            text("""
            SELECT sequence_name 
            FROM information_schema.sequences 
            WHERE sequence_schema = 'public'
        """)
        )
        sequences = [row[0] for row in result]

        for sequence in sequences:
            conn.execute(text(f'DROP SEQUENCE IF EXISTS "{sequence}" CASCADE'))

        conn.commit()
        logger.info("Dropped all existing database objects")


def _enable_vector_index(engine: Engine, logger: logging.Logger) -> None:
    """Enable vector index feature in CockroachDB.

    Args:
        engine (Engine): SQLAlchemy engine instance
        logger (logging.Logger): Logger instance for tracking operations
    """
    with engine.connect().execution_options(
        isolation_level="AUTOCOMMIT"
    ) as conn:
        conn.execute(
            text("SET CLUSTER SETTING feature.vector_index.enabled = true;")
        )
        conn.commit()
        logger.info("Enabled vector index feature")


@pytest.fixture(scope="session")
def db_engine(logger: logging.Logger) -> Generator[Engine, None, None]:
    """Create and manage the test database engine.

    This fixture creates a fresh database engine for testing, creates all tables
    using the schema.sql file, and ensures proper cleanup after tests.

    Args:
        logger (logging.Logger): Logger instance for tracking database operations

    Yields:
        Engine: SQLAlchemy engine instance for test database
    """
    logger.info("Creating test database engine")
    try:
        # Enable vector indexing
        _enable_vector_index(engine, logger)

        # Clean up any existing objects
        _drop_all_objects(engine, logger)

        # Create fresh schema
        _execute_schema_file(engine, logger)

        yield engine
    finally:
        # Clean up after tests
        _drop_all_objects(engine, logger)
        logger.info("Test database cleanup complete")


@pytest.fixture(scope="session")
def initialized_factories() -> None:
    """Hydrate factory registries once for the whole test session."""
    from ring.tests.factories.entrypoint.initialize import initialize_factories

    initialize_factories()


def _patch_factories(session: Session) -> None:
    """Initialize and patch test factories with the current database session.

    This helper function ensures all test factories are properly configured
    with the current database session for test data creation.

    Args:
        session (Session): Current database session
    """
    for factory in ALL_FACTORIES:
        factory._meta.sqlalchemy_session = session


@pytest.fixture(scope="function")
def db_session(
    db_engine: Engine, initialized_factories: None, logger: logging.Logger
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

    _patch_factories(session)

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


@pytest.fixture(autouse=True)
def mock_text_embedding() -> Generator[None, None, None]:
    """Automatically patch the text embedding function for all tests.

    This fixture provides a consistent mock embedding vector for all tests,
    ensuring deterministic behavior in tests that use text embeddings.

    Yields:
        None: The fixture yields nothing, but patches the function during test execution
    """
    # Create a mock embedding vector of 768 dimensions (standard size)
    mock_embedding = [0.1] * 768

    with patch(
        "ring.search.crud.hybrid_search._generate_text_embedding",
        return_value=mock_embedding,
    ):
        yield
