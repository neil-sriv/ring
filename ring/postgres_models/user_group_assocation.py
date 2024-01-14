from sqlalchemy import Column, Table, String, ForeignKey

from ring.fast import Base


user_group_association = Table(
    "user_group_assocation",
    Base.metadata,
    Column("user_api_id", String, ForeignKey("users.api_identifier")),
    Column("group_api_id", String, ForeignKey("groups.api_identifier")),
)
