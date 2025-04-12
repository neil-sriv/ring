"""CreatedAt mixin for SQLAlchemy models.

This module provides a mixin class that automatically adds and manages a creation
timestamp column for database models. The timestamp is set to the current time when
a record is created and cannot be modified afterwards.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class CreatedAtMixin:
    """SQLAlchemy mixin for adding creation timestamp to models.

    Automatically adds and manages a created_at timestamp column for database models.
    The timestamp is set to the current time when a record is created and cannot be
    modified afterwards.

    Attributes:
        created_at (Mapped[datetime]): DateTime column with timezone support,
            non-nullable, indexed, defaults to current timestamp
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        server_default=func.now(),
    )
