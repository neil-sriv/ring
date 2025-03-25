from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text
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

    :param id: Primary key identifier
    :type id: Mapped[int]
    :param api_identifier: Unique API identifier for the question
    :type api_identifier: Mapped[str]
    :param responses: List of responses to this question
    :type responses: Mapped[list[Response]]
    :param question_text: The actual text content of the question
    :type question_text: Mapped[str]
    :param author: User who authored the question, optional
    :type author: Mapped[User | None]
    :param letter: Letter to which this question belongs
    :type letter: Mapped[Letter]
    """

    __tablename__ = "question"

    API_ID_PREFIX = "qstn"
    PYDANTIC_MODEL = QuestionLinked

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    api_identifier: Mapped[str] = mapped_column(unique=True, index=True)

    responses: Mapped[list["Response"]] = relationship(
        back_populates="question", cascade="all"
    )

    question_text: Mapped[str] = mapped_column(Text)
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

        :param letter: Letter to which this question belongs
        :type letter: Letter
        :param question_text: The actual text content of the question
        :type question_text: str
        :param author: User who authored the question, defaults to None
        :type author: User | None
        :return: None
        :rtype: None
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

        :param letter: Letter to which this question belongs
        :type letter: Letter
        :param question_text: The actual text content of the question
        :type question_text: str
        :param author: User who authored the question, defaults to None
        :type author: User | None
        :return: New Question instance
        :rtype: Question
        """
        question = cls(letter, question_text, author)
        return question

    @hybrid_property
    def responders(self) -> list[User]:
        """Get list of users who have responded to this question.

        :return: List of users who have submitted responses
        :rtype: list[User]
        """
        respondents = {response.participant for response in self.responses}
        return list(respondents)
