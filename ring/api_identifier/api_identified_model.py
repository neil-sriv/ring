from typing import Optional
from uuid import uuid4
from sqlalchemy.orm import mapped_column, Mapped


class APIIdentified:
    API_ID_PREFIX: str

    api_identifier: Mapped[str] = mapped_column(unique=True, index=True)

    def __init__(self, api_prefix: Optional[str] = None) -> None:
        assert isinstance(self, APIIdentified), "APIIdentified must be used as a mixin"
        prefix = api_prefix or getattr(self, "API_ID_PREFIX", None)
        if not prefix:
            raise ValueError("API_ID_PREFIX must be set on the class")

        self.api_identifier = f"{prefix}_{uuid4()}"
