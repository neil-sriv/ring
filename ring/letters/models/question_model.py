"""SQLAlchemy model for question management.

This module defines the Question model, which represents a text prompt that can be
answered by letter participants. Each question belongs to a letter and can have
multiple responses from different users.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ring.api_identifier.api_identified_model import APIIdentified
from ring.created_at import CreatedAtMixin
from ring.parties.models.user_model import User
from ring.ring_pydantic.linked_schemas import QuestionLinked
from ring.ring_pydantic.pydantic_model import PydanticModel
from ring.sqlalchemy_base import Base

if TYPE_CHECKING:
    from ring.letters.models.letter_model import Letter
    from ring.letters.models.response_model import Response


class Question(Base, APIIdentified, PydanticModel, CreatedAtMixin):
    """SQLAlchemy model representing a question within a letter.

    A question is a text prompt that can be answered by letter participants.
    Each question belongs to a letter and can have multiple responses.

    Attributes:
        id (Mapped[int]): Primary key identifier
        api_identifier (Mapped[str]): Unique API identifier for the question
        responses (Mapped[list[Response]]): List of responses to this question
        question_text (Mapped[str]): The actual text content of the question
        author (Mapped[User | None]): User who authored the question, optional
        letter (Mapped[Letter]): Letter to which this question belongs
    """

    __tablename__ = "question"

    API_ID_PREFIX = "qstn"
    PYDANTIC_MODEL = QuestionLinked

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    api_identifier: Mapped[str] = mapped_column(unique=True, index=True)

    responses: Mapped[list["Response"]] = relationship(
        back_populates="question", cascade="all"
    )

    question_text: Mapped[str] = mapped_column(String)
    author_id: Mapped[int] = mapped_column(
        ForeignKey("user.id"), nullable=True, default=None
    )
    author: Mapped["User | None"] = relationship()

    letter_id: Mapped[int] = mapped_column(ForeignKey("letter.id"))
    letter: Mapped["Letter"] = relationship(back_populates="questions")

    def __init__(
        self,
        letter: Letter,
        question_text: str,
        author: User | None,
    ) -> None:
        """Initialize a new Question instance.

        Args:
            letter (Letter): Letter to which this question belongs
            question_text (str): The actual text content of the question
            author (User | None): User who authored the question
        """
        APIIdentified.__init__(self)
        self.letter = letter
        self.question_text = question_text
        self.author = author

    @classmethod
    def create(
        cls, letter: Letter, question_text: str, author: User | None = None
    ) -> Question:
        """Create a new Question instance.

        Factory method to create a new question with the given parameters.

        Args:
            letter (Letter): Letter to which this question belongs
            question_text (str): The actual text content of the question
            author (User | None, optional): User who authored the question. Defaults to None.

        Returns:
            Question: New Question instance
        """
        question = cls(letter, question_text, author)
        return question

    @hybrid_property
    def responders(self) -> list[User]:
        """Get list of users who have responded to this question.

        Returns:
            list[User]: List of users who have submitted responses
        """
        respondents = {response.participant for response in self.responses}
        return list(respondents)
