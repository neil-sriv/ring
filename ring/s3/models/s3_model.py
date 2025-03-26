"""SQLAlchemy models for S3-stored files.

This module defines models for files stored in S3, including a base S3File model
and specialized types like Image. It handles the mapping between database records
and S3 storage locations.
"""

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
    """Base model for files stored in S3.

    This model represents a file stored in S3 and provides functionality to
    generate qualified URLs for accessing the file through CloudFront.

    Attributes:
        id (int): Primary key
        type (str): Polymorphic discriminator for file type
        s3_url (str): S3 key/path for the file
    """

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
        """Generate a CloudFront URL for the file.

        Returns:
            str: Full CloudFront URL for accessing the file
        """
        return "https://du32exnxihxuf.cloudfront.net/" + self.s3_url


class MediaType(StrEnum):
    """Enumeration of supported media types.

    Attributes:
        IMAGE: Image files (e.g., jpg, png)
        VIDEO: Video files
    """

    IMAGE = "image"
    VIDEO = "video"


class Image(S3File):
    """Model for image files stored in S3.

    This model represents an image file stored in S3 and maintains relationships
    with responses that use this image.

    Attributes:
        id (int): Primary key, also foreign key to S3File
        media_type (str): Type of media (image/video)
        parent_associations (ImageResponseAssociation): Relationships to responses using this image
    """

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
        """Initialize a new image record.

        Args:
            s3_url (str): S3 key/path for the image
            media_type (MediaType, optional): Type of media. Defaults to MediaType.IMAGE.
        """
        self.s3_url = s3_url
        self.media_type = media_type

    @classmethod
    def create(
        cls,
        s3_url: str,
        media_type: MediaType = MediaType.IMAGE,
    ) -> Image:
        """Create a new image instance.

        Factory method to create a new Image instance with the given S3 URL
        and media type.

        Args:
            s3_url (str): S3 key/path for the image
            media_type (MediaType, optional): Type of media. Defaults to MediaType.IMAGE.

        Returns:
            Image: New image instance
        """
        return Image(s3_url=s3_url, media_type=media_type)
