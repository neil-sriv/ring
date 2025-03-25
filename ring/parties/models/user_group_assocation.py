"""SQLAlchemy association table for the many-to-many relationship between users and groups.

This table represents the membership of users in groups, allowing each user to be a member
of multiple groups and each group to have multiple members. It consists of two foreign key
columns:
    - user_id: References the id column of the user table
    - group_id: References the id column of the group table
"""

from sqlalchemy import Column, ForeignKey, Integer, Table

from ring.sqlalchemy_base import Base

user_group_association = Table(
    "user_group_assocation",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("user.id")),
    Column("group_id", Integer, ForeignKey("group.id")),
)
