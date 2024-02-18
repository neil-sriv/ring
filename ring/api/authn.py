from __future__ import annotations
from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
from ring.postgres_models.user_model import User
from ring.routes import internal
from ring.dependencies import RequestDependencies, get_request_dependencies
from fastapi import HTTPException
from ring.crud import user as user_crud
from ring.pydantic_schemas import UserLinked as UserSchema
from ring.security import get_current_user


@internal.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    req_dep: RequestDependencies = Depends(get_request_dependencies),
) -> dict[str, str]:
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
    return {
        "access_token": user_crud.create_access_token(
            data={"sub": user.email},
        ),
        "token_type": "bearer",
    }


@internal.post("/me", response_model=UserSchema)
async def read_users_me(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user
