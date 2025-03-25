from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator


class UserBase(BaseModel):
    """Base schema for user-related operations.

    Attributes:
        email (str): User's email address (automatically converted to lowercase)
        name (str): User's display name
    """

    email: str
    name: str

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, email: str) -> str:
        """Validate and normalize email address.

        :param email: Raw email address
        :type email: str
        :return: Lowercase email address
        :rtype: str
        """
        return email.lower()


class UserCreate(UserBase):
    """Schema for creating a new user.

    Attributes:
        email (str): User's email address (inherited from UserBase)
        name (str): User's display name (inherited from UserBase)
        password (str): User's password (will be hashed)
    """

    password: str


class UserUpdate(BaseModel):
    """Schema for updating an existing user.

    Attributes:
        email (str | None): New email address, optional
        name (str | None): New display name, optional
    """

    email: str | None = None
    name: str | None = None


class UserUpdatePassword(BaseModel):
    """Schema for updating a user's password.

    Attributes:
        current_password (str): User's current password
        new_password (str): User's new password
    """

    current_password: str
    new_password: str


class User(UserBase):
    """Schema representing a user in the system.

    Attributes:
        email (str): User's email address (inherited from UserBase)
        name (str): User's display name (inherited from UserBase)
        api_identifier (str): Unique API identifier for the user
    """

    model_config = ConfigDict(from_attributes=True)

    api_identifier: str


class UserUnlinked(User):
    """Schema for users without linked relationships.

    Inherits all fields from User but excludes relationship data.
    """

    pass


class NewPassword(BaseModel):
    """Schema for setting a new password (e.g., after reset).

    Attributes:
        new_password (str): User's new password
    """

    new_password: str
