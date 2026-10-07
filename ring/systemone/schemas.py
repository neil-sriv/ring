"""Request and response models for the LLM service System One route.

These mirror ``POST /systemone`` (noul, choice, and score). Question map
keys are caller names; the LLM service keeps them out of the model prompt.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, field_validator

Instructions = str | dict[str, Any] | list[Any]
State = str | dict[str, Any] | list[Any]


def _nonempty_content(value: Any, field_name: str) -> Any:
    if isinstance(value, str) and value.strip():
        return value
    if isinstance(value, (dict, list)) and len(value) > 0:
        return value
    raise ValueError(
        f"{field_name} must be a non-empty string, object, or array"
    )


class NoulCriteria(BaseModel):
    true: str | None = None
    false: str | None = None


class NoulQuestion(BaseModel):
    type: Literal["noul"]
    instructions: Instructions
    criteria: NoulCriteria | None = None

    @field_validator("instructions")
    @classmethod
    def instructions_present(cls, value: Instructions) -> Instructions:
        return _nonempty_content(value, "instructions")


class ChoiceQuestion(BaseModel):
    type: Literal["choice"]
    instructions: Instructions
    criteria: dict[str, str | None]

    @field_validator("instructions")
    @classmethod
    def instructions_present(cls, value: Instructions) -> Instructions:
        return _nonempty_content(value, "instructions")

    @field_validator("criteria")
    @classmethod
    def option_count(
        cls, value: dict[str, str | None]
    ) -> dict[str, str | None]:
        if not 1 <= len(value) <= 255:
            raise ValueError("choice criteria must contain 1 to 255 options")
        if any(not option.strip() for option in value):
            raise ValueError("choice option names must be non-empty")
        return value


class ScoreQuestion(BaseModel):
    type: Literal["score"]
    instructions: Instructions
    criteria: list[str]

    @field_validator("instructions")
    @classmethod
    def instructions_present(cls, value: Instructions) -> Instructions:
        return _nonempty_content(value, "instructions")

    @field_validator("criteria")
    @classmethod
    def level_count(cls, value: list[str]) -> list[str]:
        if not 2 <= len(value) <= 10:
            raise ValueError("score criteria must contain 2 to 10 levels")
        if any(not level.strip() for level in value):
            raise ValueError("score levels must be non-empty")
        return value


Question = Annotated[
    NoulQuestion | ChoiceQuestion | ScoreQuestion,
    Field(discriminator="type"),
]


class SystemOneRequest(BaseModel):
    state: State
    model: str = "jev-latest"
    questions: dict[str, Question]

    @field_validator("state")
    @classmethod
    def state_present(cls, value: State) -> State:
        return _nonempty_content(value, "state")

    @field_validator("questions")
    @classmethod
    def questions_present(
        cls, value: dict[str, Question]
    ) -> dict[str, Question]:
        if len(value) < 1:
            raise ValueError("questions must contain at least one question")
        return value


class Usage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0


class NoulAnswer(BaseModel):
    type: Literal["noul"] = "noul"
    noul: float = Field(ge=0, le=1)


class ChoiceAnswer(BaseModel):
    type: Literal["choice"] = "choice"
    choice: str
    probabilities: dict[str, float]
    confidence: float = Field(ge=0, le=1)


class ScoreAnswer(BaseModel):
    type: Literal["score"] = "score"
    score: float
    legend: dict[str, str]
    probabilities: dict[str, float]
    confidence: float = Field(ge=0, le=1)


Answer = Annotated[
    NoulAnswer | ChoiceAnswer | ScoreAnswer,
    Field(discriminator="type"),
]


class SystemOneResponse(BaseModel):
    model: str
    answers: dict[str, Answer]
    usage: Usage = Usage()
