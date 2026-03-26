"""SQLAlchemy association table for the many-to-many relationship between groups and designated responders.

This module defines the association table that represents which users are designated
responders for a group. When set, only these users can submit responses to questions
in the group's cyclic loops.
"""

from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Integer, Table

from ring.sqlalchemy_base import Base

group_designated_responder = Table(
    "group_designated_responder",
    Base.metadata,
    Column("group_id", Integer, ForeignKey("group.id")),
    Column("user_id", Integer, ForeignKey("user.id")),
)
