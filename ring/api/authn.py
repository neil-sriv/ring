from __future__ import annotations
from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
from ring.postgres_models.user_model import User
from ring.pydantic_schemas.token import Token
from ring.routes import internal
from ring.dependencies import (
    AuthenticatedRequestDependencies,
    RequestDependenciesBase,
    get_request_dependencies,
    get_unauthenticated_request_dependencies,
)
from fastapi import HTTPException
from ring.crud import user as user_crud
from ring.pydantic_schemas import UserLinked as UserSchema
from ring.security import create_access_token


@internal.post("/me", response_model=UserSchema)
async def read_users_me(
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> User:
    return req_dep.user


@internal.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    req_dep: RequestDependenciesBase = Depends(
        get_unauthenticated_request_dependencies
    ),
) -> Token:
    user = user_crud.authenticate_user(
        req_dep.db,
        form_data.username,
        form_data.password,
    )
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Incorrect username or password",
        )
    return Token(
        access_token=create_access_token(data={"sub": user.email}),
        token_type="bearer",
    )
