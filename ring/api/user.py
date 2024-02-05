from __future__ import annotations
from typing import TYPE_CHECKING, Sequence
from fastapi import Depends
from ring.routes import internal
from ring.dependencies import get_db
from fastapi import HTTPException
from ring.crud import user as user_crud, api_identifier as api_identifier_crud
from ring.pydantic_schemas import UserLinked as UserSchema
from ring.pydantic_schemas.user import UserCreate
from ring.postgres_models.user_model import User

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


@internal.post("/user/", response_model=UserSchema)
async def create_user(user: UserCreate, db: Session = Depends(get_db)) -> User:
    db_user = user_crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user = user_crud.create_user(
        db=db,
        name=user.name,
        email=user.email,
        hashed_password=user.hashed_password,
    )
    db.commit()
    return db_user


@internal.get("/users/", response_model=Sequence[UserSchema])
async def list_users(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
) -> Sequence[User]:
    users = user_crud.get_users(db, skip=skip, limit=limit)
    return users


@internal.get("/user/{user_api_id}", response_model=UserSchema)
async def read_user(user_api_id: str, db: Session = Depends(get_db)) -> User:
    db_user = api_identifier_crud.get_model(db, User, api_id=user_api_id)
    return db_user
