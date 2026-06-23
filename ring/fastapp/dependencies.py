"""FastAPI dependency injection utilities for Ring.

This module provides dependency injection utilities for FastAPI routes, including
database sessions, user authentication, and AWS S3 client management. It uses
FastAPI's dependency injection system to provide these dependencies to route handlers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import boto3
from botocore.config import Config
from fastapi import Depends, HTTPException, WebSocket, status
from loguru import logger
from mypy_boto3_s3 import S3Client

from ring.authz.enforcer import build_stateless_enforcer
from ring.parties.crud import user as user_crud
from ring.parties.models.user_model import User
from ring.security import decode_token, oauth2_scheme
from ring.sqlalchemy_base import get_db

if TYPE_CHECKING:
    from casbin import Enforcer
    from sqlalchemy.orm import Session


@dataclass
class RequestDependenciesBase:
    """Base class for request dependencies.

    This class provides the basic dependencies needed for any request,
    authenticated or not.

    Attributes:
        db (Session): SQLAlchemy database session
    """

    db: Session


@dataclass
class AuthenticatedRequestDependencies(RequestDependenciesBase):
    """Dependencies for authenticated requests.

    This class extends the base dependencies to include the authenticated user.

    Attributes:
        db (Session): SQLAlchemy database session
        current_user (User): The authenticated user making the request
    """

    current_user: User
    _enforcer: Enforcer | None = field(default=None, init=False, repr=False)

    def get_enforcer(self) -> Enforcer:
        """Return a request-scoped Casbin enforcer, building it once if needed."""
        if self._enforcer is None:
            self._enforcer = build_stateless_enforcer(
                self.db, self.current_user.api_identifier
            )
        return self._enforcer


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user from a JWT token.

    Args:
        token (str): JWT token from the Authorization header
        db (Session): Database session

    Returns:
        User: The authenticated user

    Raises:
        HTTPException: If the token is invalid or the user is not found
    """
    user_email = decode_token(token)
    user = user_crud.get_user_by_email(db, email=user_email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_request_dependencies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AuthenticatedRequestDependencies:
    """Get dependencies for authenticated requests.

    This dependency combines a database session with an authenticated user.

    Args:
        db (Session): Database session
        current_user (User): The authenticated user

    Returns:
        AuthenticatedRequestDependencies: Combined dependencies
    """
    return AuthenticatedRequestDependencies(db=db, current_user=current_user)


async def get_unauthenticated_request_dependencies(
    db: Session = Depends(get_db),
) -> RequestDependenciesBase:
    """Get dependencies for unauthenticated requests.

    This dependency provides a database session without requiring authentication.

    Args:
        db (Session): Database session

    Returns:
        RequestDependenciesBase: Basic request dependencies
    """
    return RequestDependenciesBase(db=db)


async def get_websocket_request_dependencies(
    websocket: WebSocket, db: Session = Depends(get_db)
) -> AuthenticatedRequestDependencies:
    """Get dependencies for authenticated WebSocket connections.

    This dependency extracts the authentication token from WebSocket query parameters
    and validates the user, providing the same interface as regular HTTP endpoints.

    Args:
        websocket (WebSocket): The WebSocket connection object

    Returns:
        AuthenticatedRequestDependencies: Combined dependencies including database and user

    Raises:
        HTTPException: If authentication fails
    """
    logger.info(f"WebSocket request: {websocket}")
    # Extract token from query parameters
    token = websocket.query_params.get("token")
    logger.info(f"WebSocket auth: token extracted: {token}")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Manually authenticate the user
        user_email = decode_token(token)
        current_user = user_crud.get_user_by_email(db, email=user_email)

        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return AuthenticatedRequestDependencies(
            db=db, current_user=current_user
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_s3_client_dependencies() -> S3Client:
    """Get an AWS S3 client with timeout configuration.

    Returns:
        S3Client: Boto3 S3 client with configured timeouts
    """
    s3_config = Config(
        connect_timeout=60,  # 60 seconds to establish connection
        read_timeout=300,  # 5 minutes for read operations (uploads/downloads)
        retries={"max_attempts": 3, "mode": "standard"},
    )
    return boto3.client("s3", config=s3_config)  # type: ignore
