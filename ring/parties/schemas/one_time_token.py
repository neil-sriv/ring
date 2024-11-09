from typing import Any

from pydantic import Field, computed_field


class WithTokenMixin:
    one_time_token: Any = Field(exclude=True)

    @computed_field
    @property
    def token(self) -> str:
        return self.one_time_token.token

    @computed_field
    @property
    def is_expired(self) -> bool:
        return self.one_time_token.is_expired
