from __future__ import annotations
from typing import Sequence
from fastapi import APIRouter, Depends
from ring.dependencies import (
    AuthenticatedRequestDependencies,
    RequestDependenciesBase,
    get_request_dependencies,
    get_unauthenticated_request_dependencies,
)
from fastapi import HTTPException
from ring.crud import user as user_crud, api_identifier as api_identifier_crud
from ring.pydantic_schemas import UserLinked as UserSchema
from ring.pydantic_schemas.user import UserCreate, UserUpdate
from ring.postgres_models.user_model import User

router = APIRouter()


@router.get("/me", response_model=UserSchema)
async def read_user_me(
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> User:
    return req_dep.current_user


@router.post("/user", response_model=UserSchema)
async def create_user(
    user: UserCreate,
    req_dep: RequestDependenciesBase = Depends(
        get_unauthenticated_request_dependencies,
    ),
) -> User:
    db_user = user_crud.get_user_by_email(req_dep.db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user = user_crud.create_user(
        db=req_dep.db,
        name=user.name,
        email=user.email,
        password=user.password,
    )
    req_dep.db.commit()
    return db_user


@router.get("/users", response_model=Sequence[UserSchema])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Sequence[User]:
    users = user_crud.get_users(req_dep.db, skip=skip, limit=limit)
    return users


@router.get("/user/{user_api_id}", response_model=UserSchema)
async def read_user_by_id(
    user_api_id: str,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> User:
    db_user = api_identifier_crud.get_model(
        req_dep.db,
        User,
        api_id=user_api_id,
    )
    return db_user


@router.patch("/me", deprecated=True)
def update_user_me(
    current_user_update_data: UserUpdate,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> None:
    """
    Update own user.
    """
    raise NotImplementedError()


@router.patch("/me/password", deprecated=True)
def update_password_me() -> None:
    """
    Update own password.
    """
    raise NotImplementedError()


@router.delete("/me", deprecated=True)
def delete_user_me() -> None:
    """
    Delete own user.
    """
    raise NotImplementedError()


@router.post("/signup", deprecated=True)
def register_user() -> None:
    """
    Create new user without the need to be logged in.
    """
    raise NotImplementedError()


@router.patch("/{user_id}", deprecated=True)
def update_user() -> None:
    """
    Update a user.
    """
    raise NotImplementedError()


@router.delete("/{user_id}", deprecated=True)
def delete_user() -> None:
    """
    Delete a user.
    """
    raise NotImplementedError()
