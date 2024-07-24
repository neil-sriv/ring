from typing import Any
from pydantic import Field, computed_field


class WithImageMixin:
    image_associations: list[Any] = Field(exclude=True)

    @computed_field
    @property
    def image_urls(self) -> list[str]:
        return [assoc.image.s3_url for assoc in self.image_associations]
