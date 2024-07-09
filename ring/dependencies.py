from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

import boto3

from fastapi import Depends, HTTPException, status
from mypy_boto3_s3 import S3Client
from ring.security import decode_token, oauth2_scheme
from ring.crud import user as user_crud
from ring.postgres_models.user_model import User
from ring.sqlalchemy_base import get_db

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


@dataclass
class RequestDependenciesBase:
    db: Session


@dataclass
class AuthenticatedRequestDependencies(RequestDependenciesBase):
    current_user: User


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
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
    return AuthenticatedRequestDependencies(db=db, current_user=current_user)


async def get_unauthenticated_request_dependencies(
    db: Session = Depends(get_db),
) -> RequestDependenciesBase:
    return RequestDependenciesBase(db=db)


async def get_s3_client_dependencies() -> S3Client:
    return boto3.client("s3")  # type: ignore
