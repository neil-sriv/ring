from __future__ import annotations
from typing import TYPE_CHECKING, List
from sqlalchemy import ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from ring.api_identifier.api_identified_model import APIIdentified

from ring.ring_pydantic.pydantic_model import PydanticModel
from ring.ring_pydantic.linked_schemas import ResponseLinked
from ring.sqlalchemy_base import Base

if TYPE_CHECKING:
    from ring.parties.models.user_model import User
    from ring.letters.models.question_model import Question
    from ring.s3.models.s3_model import Image


class ImageResponseAssociation(Base):
    __tablename__ = "image_response_assocation"

    image_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("image.id"), primary_key=True
    )
    response_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("response.id"),
        primary_key=True,
    )

    image: Mapped["Image"] = relationship(back_populates="parent_associations")
    response: Mapped["Response"] = relationship(
        back_populates="image_associations",
    )


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
    # images: Mapped[List["Image"]] = relationship(
    #     secondary=ImageResponseAssociation.__table__,
    # )
    image_associations: Mapped[List[ImageResponseAssociation]] = relationship(
        back_populates="response", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint(
            "participant_id", "question_id", name="participant_question_unique"
        ),
    )

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
