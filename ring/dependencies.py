"""FastAPI dependency injection utilities for Ring.

This module provides dependency injection utilities for FastAPI routes, including
database sessions, user authentication, and AWS S3 client management. It uses
FastAPI's dependency injection system to provide these dependencies to route handlers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import boto3
from fastapi import Depends, HTTPException, status
from mypy_boto3_s3 import S3Client

from ring.parties.crud import user as user_crud
from ring.parties.models.user_model import User
from ring.security import decode_token, oauth2_scheme
from ring.sqlalchemy_base import get_db

if TYPE_CHECKING:
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


async def a_get_s3_client_dependencies() -> S3Client:
    """Get an asynchronous AWS S3 client.

    Returns:
        S3Client: Boto3 S3 client for asynchronous operations
    """
    return boto3.client("s3")  # type: ignore


def get_s3_client_dependencies() -> S3Client:
    """Get a synchronous AWS S3 client.

    Returns:
        S3Client: Boto3 S3 client for synchronous operations
    """
    return boto3.client("s3")  # type: ignore
