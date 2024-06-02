from __future__ import annotations
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from ring.pydantic_schemas.token import Token
from ring.dependencies import (
    RequestDependenciesBase,
    get_unauthenticated_request_dependencies,
)
from fastapi import HTTPException
from ring.crud import user as user_crud
from ring.security import create_access_token

router = APIRouter()


@router.post("/login/access-token")
async def login_access_token(
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


@router.post("/login/test-token", deprecated=True)
def test_token() -> None:
    """
    Test access token
    """
    raise NotImplementedError()


@router.post("/password-recovery/{email}", deprecated=True)
def recover_password(email: str) -> None:
    """
    Password Recovery
    """
    raise NotImplementedError()


@router.post("/reset-password/", deprecated=True)
def reset_password() -> None:
    """
    Reset password
    """
    raise NotImplementedError()


@router.post("/password-recovery-html-content/{email}", deprecated=True)
def recover_password_html_content(email: str) -> None:
    """
    HTML Content for Password Recovery
    """
    raise NotImplementedError()
