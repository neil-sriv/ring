from pydantic import BaseModel


class PydanticModel:
    PYDANTIC_MODEL: type[BaseModel]

    def __repr__(self) -> str:
        if self.PYDANTIC_MODEL:
            return str(self.PYDANTIC_MODEL.model_validate(self))
        return super().__repr__()
