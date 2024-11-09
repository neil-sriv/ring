from typing import Any

from pydantic import BaseModel, Field, computed_field

from ring.s3.models.s3_model import MediaType


class Image(BaseModel):
    s3_url: str
    media_type: MediaType


class WithImageMixin:
    image_associations: list[Any] = Field(exclude=True)

    @computed_field
    @property
    def images(self) -> list[Image]:
        return [assoc.image for assoc in self.image_associations]
