from __future__ import annotations

from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException

from ring.api_identifier import util as api_identifier_crud
from ring.fastapp.dependencies import (
    AuthenticatedRequestDependencies,
    RequestDependenciesBase,
    get_request_dependencies,
    get_unauthenticated_request_dependencies,
)
from ring.parties.crud import (
    group as group_crud,
)
from ring.parties.crud import (
    invite as invite_crud,
)
from ring.parties.crud import (
    user as user_crud,
)
from ring.parties.crud.one_time_token import (
    TokenAlreadyUsedError,
    TokenExpiredError,
)
from ring.parties.models.user_model import User
from ring.parties.schemas.user import (
    UserCreate,
    UserUpdate,
    UserUpdatePassword,
)
from ring.ring_pydantic.core import ResponseMessage
from ring.ring_pydantic.linked_schemas import UserMe, UserUnlinked

router = APIRouter()


@router.get("/me", response_model=UserMe)
async def read_user_me(
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> User:
    """Get the current authenticated user's information.

    Args:
        req_dep (AuthenticatedRequestDependencies): Request dependencies

    Returns:
        User: Current user's information
    """
    return req_dep.current_user


@router.post(
    "/user", response_model=UserUnlinked, deprecated=True, status_code=201
)
async def create_user(
    user: UserCreate,
    req_dep: RequestDependenciesBase = Depends(
        get_unauthenticated_request_dependencies,
    ),
) -> User:
    """Create a new user (deprecated).

    Args:
        user (UserCreate): User creation parameters
        req_dep (RequestDependenciesBase): Request dependencies

    Returns:
        User: Created user

    Raises:
        HTTPException: If email is already registered

    Note:
        This endpoint is deprecated. Use /register/{token} instead.
    """
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


@router.post("/register/{token}", response_model=UserUnlinked)
async def register_user(
    token: str,
    user: UserCreate,
    req_dep: RequestDependenciesBase = Depends(
        get_unauthenticated_request_dependencies,
    ),
) -> User:
    """Register a new user with an invite token.

    Args:
        token (str): Invite token
        user (UserCreate): User creation parameters
        req_dep (RequestDependenciesBase): Request dependencies

    Returns:
        User: Created user

    Raises:
        HTTPException: If token is invalid, expired, already used, or email mismatch
    """
    try:
        db_invite = invite_crud.get_invite_by_token(req_dep.db, token)
    except (TokenAlreadyUsedError, TokenExpiredError):
        raise HTTPException(status_code=400, detail="Invalid token")
    if not db_invite or db_invite.one_time_token.used:
        raise HTTPException(status_code=400, detail="Invalid token")

    if user.email != db_invite.email:
        raise HTTPException(status_code=400, detail="Email mismatch")
    db_user = user_crud.get_user_by_email(req_dep.db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    db_user = user_crud.create_user(
        db=req_dep.db, name=user.name, email=user.email, password=user.password
    )
    db_group = db_invite.group
    db_invite.one_time_token.used = True
    req_dep.db.flush()
    group_crud.add_member(
        req_dep.db, db_group.api_identifier, db_user.api_identifier
    )
    req_dep.db.commit()
    return db_user


@router.get("/users", response_model=Sequence[UserUnlinked])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Sequence[User]:
    """Get a list of users with pagination.

    Args:
        skip (int, optional): Number of records to skip. Defaults to 0.
        limit (int, optional): Maximum number of records to return. Defaults to 100.
        req_dep (AuthenticatedRequestDependencies): Request dependencies

    Returns:
        Sequence[User]: List of users
    """
    users = user_crud.get_users(req_dep.db, skip=skip, limit=limit)
    return users


@router.get("/user/{user_api_id}", response_model=UserUnlinked)
async def read_user_by_id(
    user_api_id: str,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> User:
    """Get a user by their API identifier.

    Args:
        user_api_id (str): API identifier of the user
        req_dep (AuthenticatedRequestDependencies): Request dependencies

    Returns:
        User: User information

    Raises:
        HTTPException: If user not found
    """
    db_user = api_identifier_crud.get_model(
        req_dep.db,
        User,
        api_id=user_api_id,
    )
    return db_user


@router.patch(
    "/me",
    response_model=UserMe,
)
async def update_user_me(
    current_user_update_data: UserUpdate,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> User:
    """Update current user's information.

    Args:
        current_user_update_data (UserUpdate): User update parameters
        req_dep (AuthenticatedRequestDependencies): Request dependencies

    Returns:
        User: Updated user information

    Raises:
        HTTPException: If new email is already registered by another user
    """
    if current_user_update_data.email:
        db_user = user_crud.get_user_by_email(
            req_dep.db,
            email=current_user_update_data.email,
        )
        if db_user and db_user.id != req_dep.current_user.id:
            raise HTTPException(
                status_code=400,
                detail="Email already registered",
            )
        req_dep.current_user.email = current_user_update_data.email
    if current_user_update_data.name:
        req_dep.current_user.name = current_user_update_data.name
    req_dep.db.commit()
    return req_dep.current_user


@router.patch("/me/password", response_model=ResponseMessage)
async def update_password_me(
    update_password_data: UserUpdatePassword,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> ResponseMessage:
    """Update current user's password.

    Args:
        update_password_data (UserUpdatePassword): Password update parameters
        req_dep (AuthenticatedRequestDependencies): Request dependencies

    Returns:
        ResponseMessage: Success message

    Raises:
        HTTPException: If current password is incorrect or new password is same as current
    """
    if not user_crud._verify_password(
        update_password_data.current_password,
        req_dep.current_user.hashed_password,
    ):
        raise HTTPException(status_code=400, detail="Incorrect password")
    if (
        update_password_data.current_password
        == update_password_data.new_password
    ):
        raise HTTPException(
            status_code=400,
            detail="New password must be different from the current password",
        )

    hashed_password = user_crud.get_password_hash(
        update_password_data.new_password
    )
    req_dep.current_user.hashed_password = hashed_password
    req_dep.db.commit()
    return ResponseMessage(message="Password updated successfully")


@router.patch("/{user_api_id}/admin", response_model=ResponseMessage)
async def update_user_admin(
    user_api_id: str,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies
    ),
) -> ResponseMessage:
    """Update a user's admin status.

    Args:
        user_api_id (str): API identifier of the user to update
        req_dep (AuthenticatedRequestDependencies): Request dependencies

    Returns:
        ResponseMessage: Success message

    Raises:
        HTTPException: If user is not an admin
    """
    if not req_dep.current_user.admin:
        raise HTTPException(status_code=403, detail="Unauthorized")
    user = api_identifier_crud.get_model(
        req_dep.db,
        User,
        api_id=user_api_id,
    )
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.admin:
        raise HTTPException(status_code=400, detail="User is already an admin")
    user_crud.make_user_admin(req_dep.db, user)
    req_dep.db.commit()
    return ResponseMessage(message="User admin status updated successfully")


@router.delete("/me", deprecated=True)
async def delete_user_me() -> None:
    """Delete current user (deprecated).

    Note:
        This endpoint is not implemented and is deprecated.
    """
    raise NotImplementedError()


@router.post("/signup", deprecated=True)
async def signup() -> None:
    """Sign up a new user without invitation (deprecated).

    Note:
        This endpoint is not implemented and is deprecated.
    """
    raise NotImplementedError()


@router.patch("/{user_id}", deprecated=True)
async def update_user() -> None:
    """Update any user (deprecated).

    Note:
        This endpoint is not implemented and is deprecated.
    """
    raise NotImplementedError()


@router.delete("/{user_id}", deprecated=True)
async def delete_user() -> None:
    """Delete any user (deprecated).

    Note:
        This endpoint is not implemented and is deprecated.
    """
    raise NotImplementedError()
