"""A permission grant: subject holds permission on a resource.

Subjects and resources are api identifiers, not foreign keys. Today the
subject is a user and the resource is a group or a loop (letter). A later
closure-table policy engine can reuse the same rows for genesis IdP nested
groups by expanding the subject list, and for resource inheritance by
replacing the parent walk in ``resource_and_ancestors``.
"""

from __future__ import annotations

from enum import Enum

from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ring.sqlalchemy_base import Base


class Permission(str, Enum):
    """Baseline permissions.

    ``admin`` implies ``member`` on the same resource and its descendants.
    """

    ADMIN = "admin"
    MEMBER = "member"


class PermissionGrant(Base):
    """One row: this subject holds this permission on this resource."""

    __tablename__ = "permission_grant"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    subject_api_id: Mapped[str] = mapped_column()
    resource_api_id: Mapped[str] = mapped_column(index=True)
    permission: Mapped[str] = mapped_column()

    __table_args__ = (
        UniqueConstraint(
            "subject_api_id",
            "resource_api_id",
            "permission",
            name="uq_permission_grant_subject_resource_permission",
        ),
    )

    def __init__(
        self,
        subject_api_id: str,
        resource_api_id: str,
        permission: str,
    ) -> None:
        self.subject_api_id = subject_api_id
        self.resource_api_id = resource_api_id
        self.permission = permission
