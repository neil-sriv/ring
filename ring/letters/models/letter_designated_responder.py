"""SQLAlchemy association table for the many-to-many relationship between letters and designated responders.

This module defines the association table that represents which users are designated
responders for a specific letter (loop). When set, only these users can submit responses
to questions in that letter. This allows per-loop responder customization, particularly
useful for adhoc loops where only a subset of group members should respond.
"""

from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Integer, Table

from ring.sqlalchemy_base import Base

letter_designated_responder = Table(
    "letter_designated_responder",
    Base.metadata,
    Column("letter_id", Integer, ForeignKey("letter.id")),
    Column("user_id", Integer, ForeignKey("user.id")),
)
