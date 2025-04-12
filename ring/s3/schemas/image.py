"""Pydantic schemas for image-related models.

This module defines Pydantic models for image data and a mixin class for models
that can have associated images.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, computed_field

from ring.s3.models.s3_model import MediaType


class Image(BaseModel):
    """Schema for image data.

    Represents an image stored in S3 with its media type.

    Attributes:
        s3_url (str): S3 key/path for the image
        media_type (MediaType): Type of media (image/video)
    """

    s3_url: str
    media_type: MediaType


class WithImageMixin:
    """Mixin class for models that can have associated images.

    This mixin provides functionality to access associated images through
    a computed property, hiding the complexity of the association table.

    Attributes:
        image_associations (list[Any]): List of image associations (excluded from serialization)
        images (list[Image]): Computed property that returns the list of associated images
    """

    image_associations: list[Any] = Field(exclude=True)

    @computed_field
    @property
    def images(self) -> list[Image]:
        """Get the list of images associated with this model.

        Returns:
            list[Image]: List of associated images
        """
        return [assoc.image for assoc in self.image_associations]
