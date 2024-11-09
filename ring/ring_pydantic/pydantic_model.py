import json

from pydantic import BaseModel


class PydanticModel:
    PYDANTIC_MODEL: type[BaseModel]

    def to_pydantic(self) -> BaseModel:
        return self.PYDANTIC_MODEL.model_validate(self)

    def __str__(self) -> str:
        if self.PYDANTIC_MODEL:
            return str(self.PYDANTIC_MODEL.model_validate(self).model_dump())
        return super().__str__()

    # def __repr__(self) -> str:
    #     if self.PYDANTIC_MODEL:
    #         return str(self.PYDANTIC_MODEL.model_validate(self).model_dump())
    #     return super().__repr__()

    def __repr__(self) -> str:
        return json.dumps(self.__dict__, indent=4, default=str)
