from sqlalchemy import Column, ForeignKey, Integer, Table

from ring.sqlalchemy_base import Base

user_group_association = Table(
    "user_group_assocation",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("user.id")),
    Column("group_id", Integer, ForeignKey("group.id")),
)
