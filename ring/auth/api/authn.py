"""Authentication API endpoints.

This module provides FastAPI endpoints for user authentication, including login,
password reset, token validation, and token refresh. It handles user credentials,
JWT tokens, and password recovery workflows.
"""

from __future__ import annotations

from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from ring.api_identifier.util import get_model
from ring.async_scheduler.scheduler import scheduler
from ring.auth.schemas.token import RefreshTokenRequest, Token
from ring.fastapp.dependencies import (
    RequestDependenciesBase,
    get_request_dependencies,
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
from ring.parties.models.user_model import User
from ring.parties.schemas.user import NewPassword
from ring.ring_pydantic.core import ResponseMessage
from ring.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)

router = APIRouter()


@router.post("/login/access-token")
async def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    req_dep: RequestDependenciesBase = Depends(
        get_unauthenticated_request_dependencies
    ),
) -> Token:
    """Authenticate user and generate access and refresh tokens.

    Validates user credentials and generates JWT access and refresh tokens
    for authenticated sessions. The access token is short-lived (15 minutes)
    while the refresh token is longer-lived (30 days).

    Args:
        form_data (OAuth2PasswordRequestForm): OAuth2 password request form containing username and password
        req_dep (RequestDependenciesBase): Request dependencies including database session

    Returns:
        Token: JWT access and refresh tokens with bearer type

    Raises:
        HTTPException: 400 if credentials are invalid
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
        refresh_token=create_refresh_token(data={"sub": user.email}),
        token_type="bearer",
    )


@router.post("/login/refresh-token")
async def refresh_access_token(
    refresh_request: RefreshTokenRequest,
    req_dep: RequestDependenciesBase = Depends(
        get_unauthenticated_request_dependencies
    ),
) -> Token:
    """Refresh access token using a valid refresh token.

    Validates the refresh token and generates new access and refresh tokens.
    This allows users to maintain their session without re-authenticating,
    as long as their refresh token is still valid.

    Args:
        refresh_request (RefreshTokenRequest): Request containing the refresh token
        req_dep (RequestDependenciesBase): Request dependencies including database session

    Returns:
        Token: New JWT access and refresh tokens with bearer type

    Raises:
        HTTPException: 401 if refresh token is invalid, expired, or user not found
    """
    email = decode_refresh_token(refresh_request.refresh_token)

    # Verify the user still exists and is active
    user = user_crud.get_user_by_email(req_dep.db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return Token(
        access_token=create_access_token(data={"sub": user.email}),
        refresh_token=create_refresh_token(data={"sub": user.email}),
        token_type="bearer",
    )


@router.post("/impersonate-user-token")
async def impersonate_user_token(
    user_api_id: str,
    req_dep: RequestDependenciesBase = Depends(get_request_dependencies),
) -> Token:
    if not req_dep.current_user.admin:
        raise HTTPException(status_code=403, detail="Unauthorized")
    user = get_model(
        req_dep.db,
        User,
        api_id=user_api_id,
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return Token(
        access_token=create_access_token(data={"sub": user.email}),
        refresh_token=create_refresh_token(data={"sub": user.email}),
        token_type="bearer",
    )


@router.post("/login/test-token", deprecated=True)
async def test_token() -> None:
    """Test endpoint for validating access tokens.

    This endpoint is deprecated and will be removed in future versions.

    Raises:
        NotImplementedError: Always raises this error as the endpoint is deprecated
    """
    raise NotImplementedError()


@router.post("/reset-password:request/{email}", response_model=ResponseMessage)
async def reset_password_request(
    email: str,
    req_dep: RequestDependenciesBase = Depends(
        get_unauthenticated_request_dependencies
    ),
) -> ResponseMessage:
    """Initiate password reset process for a user.

    Generates a one-time token and sends a password reset email to the user.

    Args:
        email (str): User's email address
        req_dep (RequestDependenciesBase): Request dependencies including database session

    Returns:
        ResponseMessage: Confirmation message of email sent

    Raises:
        HTTPException: 400 if user with email doesn't exist
    """
    db_user = user_crud.get_user_by_email(req_dep.db, email)
    if not db_user:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="User with this email does not exist",
        )
    ott = generate_token(TokenType.PASSWORD_RESET, email)
    req_dep.db.add(ott)
    scheduler.add_job(
        email_password_reset,
        args=[email, ott.token],
    )
    req_dep.db.commit()
    return ResponseMessage(message="Password recovery email sent")


@router.post("/reset-password/{token}", response_model=ResponseMessage)
async def reset_password(
    token: str,
    new_password_data: NewPassword,
    req_dep: RequestDependenciesBase = Depends(
        get_unauthenticated_request_dependencies
    ),
) -> ResponseMessage:
    """Reset user's password using a valid reset token.

    Validates the reset token and updates the user's password if token is valid.

    Args:
        token (str): Password reset token
        new_password_data (NewPassword): New password data
        req_dep (RequestDependenciesBase): Request dependencies including database session

    Returns:
        ResponseMessage: Confirmation message of password update

    Raises:
        HTTPException: 400 if token is invalid, expired, or already used
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
async def recover_password_html_content(email: str) -> None:
    """Generate HTML content for password recovery email.

    This endpoint is deprecated and will be removed in future versions.

    Args:
        email (str): User's email address

    Raises:
        NotImplementedError: Always raises this error as the endpoint is deprecated
    """
    raise NotImplementedError()
