from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ring.api_identifier.api_identified_model import APIIdentified
from ring.created_at import CreatedAtMixin
from ring.sqlalchemy_base import Base

if TYPE_CHECKING:
    from ring.parties.models.group_model import Group


class DefaultQuestion(Base, APIIdentified, CreatedAtMixin):
    """SQLAlchemy model representing a default question template for a group.

    Default questions are predefined question templates that can be used
    when creating new letters for a group.

    :param id: Primary key identifier
    :type id: Mapped[int]
    :param question_text: The text content of the default question
    :type question_text: Mapped[str]
    :param group: Group to which this default question belongs
    :type group: Mapped[Group]
    """

    __tablename__ = "default_question"

    API_ID_PREFIX = "dfqstn"
    # PYDANTIC_MODEL = QuestionLinked

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    question_text: Mapped[str] = mapped_column(Text)
    group_id: Mapped[int] = mapped_column(ForeignKey("group.id"))
    group: Mapped["Group"] = relationship(back_populates="default_questions")

    def __init__(
        self,
        question_text: str,
        group: Group,
    ) -> None:
        """Initialize a new DefaultQuestion instance.

        :param question_text: The text content of the default question
        :type question_text: str
        :param group: Group to which this default question belongs
        :type group: Group
        :return: None
        :rtype: None
        """
        APIIdentified.__init__(self)
        self.question_text = question_text
        self.group = group

    @classmethod
    def create(cls, question_text: str, group: Group) -> DefaultQuestion:
        """Create a new DefaultQuestion instance.

        Factory method to create a new default question with the given parameters.

        :param question_text: The text content of the default question
        :type question_text: str
        :param group: Group to which this default question belongs
        :type group: Group
        :return: New DefaultQuestion instance
        :rtype: DefaultQuestion
        """
        default_question = cls(question_text, group)
        return default_question
