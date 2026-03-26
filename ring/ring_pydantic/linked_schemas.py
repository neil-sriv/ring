"""Pydantic models for linked entity responses.

This module defines Pydantic models that include relationships between different
entities in the system. These models are used for API responses where related
entities need to be included in the response.
"""

from __future__ import annotations

from typing import Any, Literal, Optional, Union

from loguru import logger
from pydantic import (
    BaseModel,
    Field,
    ValidationInfo,
    computed_field,
    field_validator,
    model_validator,
    validator,
)

from ring.letters.schemas.letter import Letter, LetterUnlinked
from ring.letters.schemas.question import Question, QuestionUnlinked
from ring.letters.schemas.response import Response, ResponseUnlinked
from ring.notifications.schemas.subscription import Subscription
from ring.parties.schemas.group import Group, GroupUnlinked
from ring.parties.schemas.invite import Invite
from ring.parties.schemas.user import User, UserUnlinked
from ring.s3.schemas.image import WithImageMixin
from ring.tasks.schemas.schedule import Schedule, ScheduleUnlinked
from ring.tasks.schemas.task import TaskUnlinked


class UserLinked(User):
    """User model with linked relationships.

    Extends the base User model to include related groups and responses.

    Attributes:
        groups (list[GroupUnlinked]): Groups the user is a member of
        responses (list[ResponseUnlinked]): User's responses to questions
    """

    groups: list["GroupUnlinked"]
    responses: list["ResponseUnlinked"]


class GroupLinked(Group):
    """Group model with linked relationships.

    Extends the base Group model to include members, letters, and other related data.

    Attributes:
        members (list[UserUnlinked]): Users who are members of the group
        letters (list[LetterUnlinked]): Letters associated with the group
        schedule (Optional[ScheduleUnlinked]): Group's schedule, if any
        admin (UserUnlinked): The group administrator
        default_questions (list[QuestionUnlinked]): Default questions for group letters
        responder_allowlist (list[UserUnlinked]): If non-empty, only these members may
            respond on cyclic loops; if empty, everyone in the group may respond
    """

    members: list["UserUnlinked"]
    letters: list["LetterUnlinked"]
    schedule: Optional["ScheduleUnlinked"]
    admin: "UserUnlinked"
    default_questions: list["QuestionUnlinked"]
    responder_allowlist: list["UserUnlinked"]


class ScheduleLinked(Schedule):
    """Schedule model with linked relationships.

    Extends the base Schedule model to include the associated group and tasks.

    Attributes:
        group (GroupUnlinked): The group this schedule belongs to
        tasks (list[TaskUnlinked]): Tasks in the schedule
    """

    group: "GroupUnlinked"
    tasks: list["TaskUnlinked"]


# class TaskLinked(Task):
#     schedule: "ScheduleUnlinked"


class LetterLinked(Letter):
    """Letter model with linked relationships.

    Extends the base Letter model to include participants, group, and questions.

    Attributes:
        participants (list[UserUnlinked]): Users participating in the letter
        group (GroupUnlinked): Group the letter belongs to
        questions (list[QuestionLinked]): Questions in the letter
    """

    participants: list["UserUnlinked"]
    group: "GroupUnlinked"
    questions: list["QuestionLinked"]


class MinimalLetter(Letter):
    """Minimal letter model.

    Attributes:
        group (GroupUnlinked): Group the letter belongs to
    """

    group: "GroupUnlinked"


class PublicLetter(Letter):
    """Public letter model with linked relationships.

    A version of the Letter model that includes public information about participants
    and responses.

    Attributes:
        group (GroupUnlinked): Group the letter belongs to
        questions (list[PublicQuestion]): Questions with public responses
        responders (list[UserUnlinked]): Users who have responded
        participants (list[UserUnlinked]): All participants in the letter
        responder_allowlist (list[UserUnlinked]): If non-empty, overrides group
            default for who may respond on this letter
        effective_responders (list[UserUnlinked]): Members who may submit responses
    """

    group: "GroupUnlinked"
    questions: list["PublicQuestion"]
    responders: list["UserUnlinked"]
    participants: list["UserUnlinked"]
    responder_allowlist: list["UserUnlinked"]
    effective_responders: list["UserUnlinked"]


class DashboardLetters(BaseModel):
    """Model for the letters dashboard view.

    Groups letters by their status for dashboard display.

    Attributes:
        upcoming (list[PublicLetter]): Letters scheduled for the future
        in_progress (list[PublicLetter]): Currently active letters
        recently_completed (list[PublicLetter]): Recently finished letters
    """

    upcoming: list[PublicLetter]
    in_progress: list[PublicLetter]
    recently_completed: list[PublicLetter]


class QuestionLinked(Question):
    """Question model with linked relationships.

    Extends the base Question model to include the parent letter and responses.

    Attributes:
        letter (LetterUnlinked): Letter containing this question
        responses (list[ResponseUnlinked]): Responses to this question
    """

    letter: "LetterUnlinked"
    group: "GroupUnlinked"
    responses: list["ResponseUnlinked"]

    @model_validator(mode="before")
    @classmethod
    def set_group(cls, obj: Any) -> "QuestionLinked":
        if isinstance(obj, BaseModel):
            return obj
        obj.group = obj.letter.group
        return obj


class PublicQuestion(Question):
    """Public question model with linked relationships.

    A version of the Question model that includes public response information.

    Attributes:
        responses (list[ResponseWithParticipant]): Public responses with participant info
        author (Optional[UserUnlinked]): Question author, if available
    """

    responses: list["ResponseWithParticipant"]
    author: Optional["UserUnlinked"]


class ResponseLinked(Response, WithImageMixin):
    """Response model with linked relationships and image support.

    Extends the base Response model to include question and participant info,
    with support for attached images.

    Attributes:
        question (QuestionUnlinked): Question this response is for
        participant (UserUnlinked): User who provided the response
    """

    question: "QuestionUnlinked"
    participant: "UserUnlinked"
    letter: "LetterUnlinked"
    group: "GroupUnlinked"

    @model_validator(mode="before")
    @classmethod
    def set_letter_and_group(cls, obj: Any) -> "ResponseLinked":
        if isinstance(obj, BaseModel):
            return obj
        obj.letter = obj.question.letter
        obj.group = obj.question.letter.group
        return obj


class ResponseWithParticipant(Response, WithImageMixin):
    """Response model with participant information and image support.

    A version of the Response model that includes participant information
    and support for attached images.

    Attributes:
        participant (UserUnlinked): User who provided the response
    """

    participant: "UserUnlinked"


class InviteLinked(Invite):
    """Invite model with linked relationships.

    Extends the base Invite model to include inviter and group information.

    Attributes:
        inviter (UserUnlinked): User who created the invite
        group (GroupUnlinked): Group the invite is for
    """

    inviter: "UserUnlinked"
    group: "GroupUnlinked"


class SubscriptionLinked(Subscription):
    """Subscription model with linked relationships.

    Extends the base Subscription model to include user information.

    Attributes:
        user (UserUnlinked): User who owns the subscription
    """

    user: "UserUnlinked"


class UnknownSearchResult(BaseModel):
    """Search result model for unknown types.

    Attributes:
        type (str): Type of the model
        model (Any): The model instance
    """

    model: Any


class SearchResult(BaseModel):
    """Search result model that can hold different types of models based on type field.

    Attributes:
        model (Any): The model instance
        type (str): The type of the model
    """

    model: (
        UserLinked
        | GroupLinked
        | QuestionLinked
        | ResponseLinked
        | PublicLetter
        # | UnknownSearchResult
    )
    type: str

    @classmethod
    def from_model(cls, model: Any) -> "SearchResult":
        """Create a SearchResult from a model instance.

        Args:
            model: Any model instance that has a PYDANTIC_MODEL attribute
        """
        if not hasattr(model, "PYDANTIC_MODEL"):
            return UnknownSearchResult(model=model)

        # Convert SQLAlchemy model to Pydantic model using PYDANTIC_MODEL
        pydantic_model = model.PYDANTIC_MODEL.model_validate(model)
        return cls(model=pydantic_model, type=model.PYDANTIC_MODEL.__name__)


class SearchResponse(BaseModel):
    results: list[SearchResult]
    total: int
