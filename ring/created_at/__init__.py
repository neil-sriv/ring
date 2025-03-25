from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class CreatedAtMixin:
    """SQLAlchemy mixin for adding creation timestamp to models.

    Automatically adds and manages a created_at timestamp column for database models.
    The timestamp is set to the current time when a record is created and cannot be
    modified afterwards.

    :param created_at: Timestamp when the record was created
    :type created_at: Mapped[datetime]
    :ivar created_at: DateTime column with timezone support, non-nullable, indexed, defaults to current timestamp
    """
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        server_default=func.now(),
    )
