from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from ring.postgres_models.api_identified import APIIdentified

from ring.postgres_models.pydantic_model import PydanticModel
from ring.pydantic_schemas.linked_schemas import ResponseLinked
from ring.sqlalchemy_base import Base

if TYPE_CHECKING:
    # from ring.postgres_models.letter_model import Letter
    from ring.postgres_models.user_model import User
    from ring.postgres_models.question_model import Question


class Response(Base, APIIdentified, PydanticModel):
    __tablename__ = "response"

    API_ID_PREFIX = "rspn"
    PYDANTIC_MODEL = ResponseLinked

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    api_identifier: Mapped[str] = mapped_column(unique=True, index=True)

    participant_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    participant: Mapped["User"] = relationship(lazy=False)
    question_id: Mapped[int] = mapped_column(ForeignKey("question.id"))
    question: Mapped["Question"] = relationship(back_populates="responses")

    response_text: Mapped[str] = mapped_column(Text)
    _image_file: Mapped[str] = mapped_column(nullable=True, default=None)

    def __init__(
        self,
        participant: User,
        question: Question,
        response_text: str,
    ) -> None:
        APIIdentified.__init__(self)
        self.participant = participant
        self.question = question
        self.response_text = response_text

    @classmethod
    def create(
        cls,
        participant: User,
        question: Question,
        response_text: str,
    ) -> Response:
        response = cls(participant, question, response_text)
        return response
