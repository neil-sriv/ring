"""Receipts for late-question emails already accepted by the provider.

One row means this recipient was emailed this question. A retry of the
same window skips those pairs, so a later batch that was rejected can be
sent without mailing the people who already got it.
"""

from __future__ import annotations

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ring.sqlalchemy_base import Base


class LateQuestionEmailReceipt(Base):
    """A late question that has already been emailed to one person."""

    __tablename__ = "late_question_email_receipt"
    __table_args__ = (
        UniqueConstraint(
            "letter_id",
            "user_id",
            "question_id",
            name="uq_late_question_email_receipt",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    letter_id: Mapped[int] = mapped_column(
        ForeignKey("letter.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("question.id", ondelete="CASCADE"),
        nullable=False,
    )
