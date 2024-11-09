from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ring.sqlalchemy_base import Base

if TYPE_CHECKING:
    from ring.letters.models.response_model import ImageResponseAssociation


class S3File(Base):
    __tablename__ = "s3_file"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    type: Mapped[str]

    s3_url: Mapped[str] = mapped_column()

    __mapper_args__ = {
        "polymorphic_identity": "s3_file",
        "polymorphic_on": "type",
    }

    @hybrid_property
    def qualified_s3_url(self) -> str:
        return "https://du32exnxihxuf.cloudfront.net/" + self.s3_url


class MediaType(StrEnum):
    IMAGE = "image"
    VIDEO = "video"


class Image(S3File):
    __tablename__ = "image"

    id: Mapped[int] = mapped_column(
        ForeignKey("s3_file.id"), primary_key=True, index=True
    )
    media_type: Mapped[str] = mapped_column(nullable=False)
    # parent: Mapped["ImageResponseAssociation"] = relationship(
    #     back_populates="images",
    # )
    parent_associations: Mapped["ImageResponseAssociation"] = relationship(
        back_populates="image", overlaps="images", cascade="all, delete-orphan"
    )

    __mapper_args__ = {
        "polymorphic_identity": "image",
    }

    def __init__(
        self,
        s3_url: str,
        media_type: MediaType = MediaType.IMAGE,
    ) -> None:
        self.s3_url = s3_url
        self.media_type = media_type

    @classmethod
    def create(
        cls,
        s3_url: str,
        media_type: MediaType = MediaType.IMAGE,
    ) -> Image:
        return Image(s3_url=s3_url, media_type=media_type)
