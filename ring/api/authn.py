from __future__ import annotations
from typing import TYPE_CHECKING
from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
from ring.postgres_models.user_model import User
from ring.routes import internal
from ring.dependencies import get_db
from fastapi import HTTPException
from ring.crud import user as user_crud
from ring.pydantic_schemas import UserLinked as UserSchema
from ring.security import get_current_user

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


@internal.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    user = user_crud.authenticate_user(
        db,
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
