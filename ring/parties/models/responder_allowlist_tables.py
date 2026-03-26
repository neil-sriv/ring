"""Association tables for optional responder allowlists on groups and letters."""

from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Integer, Table

from ring.sqlalchemy_base import Base

group_responder_allowlist = Table(
    "group_responder_allowlist",
    Base.metadata,
    Column("group_id", Integer, ForeignKey("group.id"), primary_key=True),
    Column("user_id", Integer, ForeignKey("user.id"), primary_key=True),
)

letter_responder_allowlist = Table(
    "letter_responder_allowlist",
    Base.metadata,
    Column("letter_id", Integer, ForeignKey("letter.id"), primary_key=True),
    Column("user_id", Integer, ForeignKey("user.id"), primary_key=True),
)
