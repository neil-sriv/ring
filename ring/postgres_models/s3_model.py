from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ring.sqlalchemy_base import Base

if TYPE_CHECKING:
    from ring.postgres_models.response_model import ImageResponseAssociation


class S3File(Base):
    __tablename__ = "s3_file"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    type: Mapped[str]

    s3_url: Mapped[str] = mapped_column()

    __mapper_args__ = {
        "polymorphic_identity": "s3_file",
        "polymorphic_on": "type",
    }


class Image(S3File):
    __tablename__ = "image"

    id: Mapped[int] = mapped_column(
        ForeignKey("s3_file.id"), primary_key=True, index=True
    )
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
    ) -> None:
        self.s3_url = s3_url

    @classmethod
    def create(
        cls,
        s3_url: str,
    ) -> Image:
        return Image(s3_url=s3_url)
