"""SQLAlchemy association table for the many-to-many relationship between users and groups.

This module defines the association table that represents the membership of users in groups,
allowing each user to be a member of multiple groups and each group to have multiple members.
"""

from sqlalchemy import Column, ForeignKey, Integer, Table

from ring.sqlalchemy_base import Base

user_group_association = Table(
    "user_group_assocation",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("user.id")),
    Column("group_id", Integer, ForeignKey("group.id")),
)
