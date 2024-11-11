from __future__ import annotations

from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from ring.auth.schemas.token import Token
from ring.dependencies import (
    RequestDependenciesBase,
    get_unauthenticated_request_dependencies,
)
from ring.parties.crud import user as user_crud
from ring.parties.crud.authn import email_password_reset, reset_user_password
from ring.parties.crud.one_time_token import (
    generate_token,
    get_ott_by_token,
    validate_and_use_token,
)
from ring.parties.models.one_time_token_model import TokenType
from ring.parties.schemas.user import NewPassword
from ring.ring_pydantic.core import ResponseMessage
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


@router.post("/reset-password:request/{email}", response_model=ResponseMessage)
def reset_password_request(
    email: str,
    req_dep: RequestDependenciesBase = Depends(
        get_unauthenticated_request_dependencies
    ),
) -> ResponseMessage:
    """
    Password Reset Request
    """
    db_user = user_crud.get_user_by_email(req_dep.db, email)
    if not db_user:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="User with this email does not exist",
        )
    ott = generate_token(TokenType.PASSWORD_RESET, email)
    email_password_reset.delay(email, ott.token)
    return ResponseMessage(message="Password recovery email sent")


@router.post("/reset-password/{token}", response_model=ResponseMessage)
def reset_password(
    token: str,
    new_password_data: NewPassword,
    req_dep: RequestDependenciesBase = Depends(
        get_unauthenticated_request_dependencies
    ),
) -> ResponseMessage:
    """
    Reset password
    """
    ott = get_ott_by_token(req_dep.db, token)
    if not ott:
        raise HTTPException(status_code=400, detail="Invalid token")
    validate_and_use_token(req_dep.db, ott)
    db_user = user_crud.get_user_by_email(req_dep.db, ott.email)
    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid token")

    reset_user_password(db_user, new_password_data.new_password)
    req_dep.db.commit()
    return ResponseMessage(message="Password updated successfully")


@router.post("/password-recovery-html-content/{email}", deprecated=True)
def recover_password_html_content(email: str) -> None:
    """
    HTML Content for Password Recovery
    """
    raise NotImplementedError()
