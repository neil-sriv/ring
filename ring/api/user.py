from __future__ import annotations
from typing import Sequence
from fastapi import Depends
from ring.routes import internal
from ring.dependencies import (
    AuthenticatedRequestDependencies,
    RequestDependenciesBase,
    get_request_dependencies,
    get_unauthenticated_request_dependencies,
)
from fastapi import HTTPException
from ring.crud import user as user_crud, api_identifier as api_identifier_crud
from ring.pydantic_schemas import UserLinked as UserSchema
from ring.pydantic_schemas.user import UserCreate
from ring.postgres_models.user_model import User


@internal.post("/user", response_model=UserSchema)
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


@internal.get("/users", response_model=Sequence[UserSchema])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Sequence[User]:
    users = user_crud.get_users(req_dep.db, skip=skip, limit=limit)
    return users


@internal.get("/user/{user_api_id}", response_model=UserSchema)
async def read_user(
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
