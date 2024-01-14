from __future__ import annotations
from sqlalchemy import Column, ForeignKey, String, Table, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column

from ring.fast import Base
from ring.postgres_models.response_model import Response
from ring.postgres_models.user_model import User

response_to_user_association = Table(
    "response_to_user_association",
    Base.metadata,
    Column("response_api_id", String, ForeignKey("responses.api_identifier")),
    Column("user_api_id", String, ForeignKey("users.api_identifier")),
)


class Question(Base):
    __tablename__ = "response"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    api_identifier: Mapped[String] = mapped_column(unique=True, index=True)

    participants: Mapped[list["User"]] = relationship(
        secondary=response_to_user_association
    )
    responses: Mapped[list["Response"]] = relationship(back_populates="question")

    question_text: Mapped[Text] = mapped_column()
