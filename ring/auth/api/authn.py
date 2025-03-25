from __future__ import annotations

from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from ring.auth.schemas.token import Token
from ring.dependencies import (
    RequestDependenciesBase,
    get_unauthenticated_request_dependencies,
)
from ring.parties.crud import user as user_crud
from ring.parties.crud.authn import email_password_reset, reset_user_password
from ring.parties.crud.one_time_token import (
    TokenAlreadyUsedError,
    TokenExpiredError,
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
    """Authenticate user and generate access token.

    Validates user credentials and generates a JWT access token for authenticated sessions.

    :param form_data: OAuth2 password request form containing username and password
    :type form_data: OAuth2PasswordRequestForm
    :param req_dep: Request dependencies including database session
    :type req_dep: RequestDependenciesBase
    :raises HTTPException: 400 if credentials are invalid
    :return: JWT access token with bearer type
    :rtype: Token
    """
    user = user_crud.authenticate_user(
        req_dep.db,
        form_data.username,
        form_data.password,
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password",
        )
    return Token(
        access_token=create_access_token(data={"sub": user.email}),
        token_type="bearer",
    )


@router.post("/login/test-token", deprecated=True)
def test_token() -> None:
    """Test endpoint for validating access tokens.

    This endpoint is deprecated and will be removed in future versions.

    :raises NotImplementedError: Always raises this error as the endpoint is deprecated
    :return: None
    :rtype: None
    """
    raise NotImplementedError()


@router.post("/reset-password:request/{email}", response_model=ResponseMessage)
def reset_password_request(
    email: str,
    req_dep: RequestDependenciesBase = Depends(
        get_unauthenticated_request_dependencies
    ),
) -> ResponseMessage:
    """Initiate password reset process for a user.

    Generates a one-time token and sends a password reset email to the user.

    :param email: User's email address
    :type email: str
    :param req_dep: Request dependencies including database session
    :type req_dep: RequestDependenciesBase
    :raises HTTPException: 400 if user with email doesn't exist
    :return: Confirmation message of email sent
    :rtype: ResponseMessage
    """
    db_user = user_crud.get_user_by_email(req_dep.db, email)
    if not db_user:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="User with this email does not exist",
        )
    ott = generate_token(TokenType.PASSWORD_RESET, email)
    req_dep.db.add(ott)
    email_password_reset.delay(email, ott.token)
    req_dep.db.commit()
    return ResponseMessage(message="Password recovery email sent")


@router.post("/reset-password/{token}", response_model=ResponseMessage)
def reset_password(
    token: str,
    new_password_data: NewPassword,
    req_dep: RequestDependenciesBase = Depends(
        get_unauthenticated_request_dependencies
    ),
) -> ResponseMessage:
    """Reset user's password using a valid reset token.

    Validates the reset token and updates the user's password if token is valid.

    :param token: Password reset token
    :type token: str
    :param new_password_data: New password data
    :type new_password_data: NewPassword
    :param req_dep: Request dependencies including database session
    :type req_dep: RequestDependenciesBase
    :raises HTTPException: 400 if token is invalid, expired, or already used
    :return: Confirmation message of password update
    :rtype: ResponseMessage
    """
    ott = get_ott_by_token(req_dep.db, token)
    if not ott:
        raise HTTPException(status_code=400, detail="Invalid token")
    try:
        validate_and_use_token(req_dep.db, ott)
    except TokenExpiredError:
        raise HTTPException(status_code=400, detail="Token expired")
    except TokenAlreadyUsedError:
        raise HTTPException(status_code=400, detail="Token already used")
    db_user = user_crud.get_user_by_email(req_dep.db, ott.email)
    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid token")

    reset_user_password(db_user, new_password_data.new_password)
    ott.used = True
    req_dep.db.commit()
    return ResponseMessage(message="Password updated successfully")


@router.post("/password-recovery-html-content/{email}", deprecated=True)
def recover_password_html_content(email: str) -> None:
    """Generate HTML content for password recovery email.

    This endpoint is deprecated and will be removed in future versions.

    :param email: User's email address
    :type email: str
    :raises NotImplementedError: Always raises this error as the endpoint is deprecated
    :return: None
    :rtype: None
    """
    raise NotImplementedError()
