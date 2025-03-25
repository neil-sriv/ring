from __future__ import annotations

from typing import TYPE_CHECKING, List

from sqlalchemy import ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ring.api_identifier.api_identified_model import APIIdentified
from ring.created_at import CreatedAtMixin
from ring.ring_pydantic.linked_schemas import ResponseLinked
from ring.ring_pydantic.pydantic_model import PydanticModel
from ring.s3.models.s3_model import Image
from ring.sqlalchemy_base import Base

if TYPE_CHECKING:
    from ring.letters.models.question_model import Question
    from ring.parties.models.user_model import User


class ImageResponseAssociation(Base):
    """Association table model linking responses to images.

    Represents a many-to-many relationship between responses and images,
    allowing responses to have multiple associated images.

    :param image_id: Foreign key to the image table
    :type image_id: Mapped[int]
    :param response_id: Foreign key to the response table
    :type response_id: Mapped[int]
    :param image: Related Image instance
    :type image: Mapped[Image]
    :param response: Related Response instance
    :type response: Mapped[Response]
    """

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


class Response(Base, APIIdentified, PydanticModel, CreatedAtMixin):
    """SQLAlchemy model representing a response to a question.

    A response is created when a participant answers a question in a letter.
    Each response can have associated text content and images.

    :param id: Primary key identifier
    :type id: Mapped[int]
    :param api_identifier: Unique API identifier for the response
    :type api_identifier: Mapped[str]
    :param participant: User who provided the response
    :type participant: Mapped[User]
    :param question: Question being answered
    :type question: Mapped[Question]
    :param response_text: Text content of the response
    :type response_text: Mapped[str]
    :param image_associations: List of associated images through junction table
    :type image_associations: Mapped[List[ImageResponseAssociation]]
    """

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
        """Initialize a new Response instance.

        :param participant: User who provided the response
        :type participant: User
        :param question: Question being answered
        :type question: Question
        :param response_text: Text content of the response
        :type response_text: str
        :return: None
        :rtype: None
        """
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
        """Create a new Response instance.

        Factory method to create a new response with the given parameters.

        :param participant: User who provided the response
        :type participant: User
        :param question: Question being answered
        :type question: Question
        :param response_text: Text content of the response
        :type response_text: str
        :return: New Response instance
        :rtype: Response
        """
        response = cls(participant, question, response_text)
        return response
