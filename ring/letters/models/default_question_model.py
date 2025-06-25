"""SQLAlchemy model for default question templates.

This module defines the DefaultQuestion model, which represents predefined question
templates that can be automatically added to new letters for a group.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ring.api_identifier.api_identified_model import APIIdentified
from ring.api_identifier.util import APIPrefix, register_api_class
from ring.created_at import CreatedAtMixin
from ring.sqlalchemy_base import Base

if TYPE_CHECKING:
    from ring.parties.models.group_model import Group


@register_api_class(APIPrefix.DEFAULT_QUESTION)
class DefaultQuestion(Base, APIIdentified, CreatedAtMixin):
    """SQLAlchemy model representing a default question template for a group.

    Default questions are predefined question templates that can be used
    when creating new letters for a group.

    Attributes:
        id (Mapped[int]): Primary key identifier
        question_text (Mapped[str]): The text content of the default question
        group (Mapped[Group]): Group to which this default question belongs
    """

    __tablename__ = "default_question"

    API_ID_PREFIX = APIPrefix.DEFAULT_QUESTION
    # PYDANTIC_MODEL = QuestionLinked

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    question_text: Mapped[str] = mapped_column(String)
    group_id: Mapped[int] = mapped_column(ForeignKey("group.id"))
    group: Mapped["Group"] = relationship(back_populates="default_questions")

    def __init__(
        self,
        question_text: str,
        group: Group,
    ) -> None:
        """Initialize a new DefaultQuestion instance.

        Args:
            question_text (str): The text content of the default question
            group (Group): Group to which this default question belongs
        """
        APIIdentified.__init__(self)
        self.question_text = question_text
        self.group = group

    @classmethod
    def create(cls, question_text: str, group: Group) -> DefaultQuestion:
        """Create a new DefaultQuestion instance.

        Factory method to create a new default question with the given parameters.

        Args:
            question_text (str): The text content of the default question
            group (Group): Group to which this default question belongs

        Returns:
            DefaultQuestion: New DefaultQuestion instance
        """
        default_question = cls(question_text, group)
        return default_question
