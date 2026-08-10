"""Pydantic models for linked entity responses.

This module defines Pydantic models that include relationships between different
entities in the system. These models are used for API responses where related
entities need to be included in the response.
"""

from __future__ import annotations

from typing import Any, Literal, Optional, Self, Union

from loguru import logger
from pydantic import (
    BaseModel,
    Field,
    ModelWrapValidatorHandler,
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


def _populate_letter_send_threshold_fields[T: BaseModel](
    model: T, letter: Any
) -> T:
    """Add send-threshold progress fields when serializing a letter ORM object."""
    # Skip when input is already a Pydantic model (e.g. FastAPI response_model
    # re-validation). Threshold fields are only computable from ORM letters whose
    # group carries key_values, not from linked schemas like GroupUnlinked.
    if isinstance(letter, BaseModel):
        return model
    if not hasattr(letter, "group") or letter.group is None:
        return model
    if not hasattr(letter.group, "key_values"):
        return model
    from ring.letters.send_threshold import (
        effective_send_threshold_ratio,
        letter_responder_count,
        minimum_responders_required,
    )

    return model.model_copy(
        update={
            "required_responders": minimum_responders_required(letter),
            "responder_count": letter_responder_count(letter),
            "send_threshold_ratio": effective_send_threshold_ratio(
                letter.group
            ),
        }
    )


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
    """

    members: list["UserUnlinked"]
    letters: list["LetterUnlinked"]
    schedule: Optional["ScheduleUnlinked"]
    admin: "UserUnlinked"
    default_questions: list["QuestionUnlinked"]


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
        responders (list[UserUnlinked]): Users who have responded
        required_responders (int): Minimum unique responders needed before send
        responder_count (int): Current unique responder count
        send_threshold_ratio (float | None): Effective ratio gate, or null if disabled
    """

    group: "GroupUnlinked"
    responders: list["UserUnlinked"]
    required_responders: int = 0
    responder_count: int = 0
    send_threshold_ratio: float | None = None

    @model_validator(mode="wrap")
    @classmethod
    def populate_send_threshold_progress(
        cls,
        data: Any,
        handler: ModelWrapValidatorHandler[Self],
    ) -> Self:
        model = handler(data)
        return _populate_letter_send_threshold_fields(model, data)


class PublicLetter(Letter):
    """Public letter model with linked relationships.

    A version of the Letter model that includes public information about participants
    and responses.

    Attributes:
        group (GroupUnlinked): Group the letter belongs to
        questions (list[PublicQuestion]): Questions with public responses
        responders (list[UserUnlinked]): Users who have responded
        participants (list[UserUnlinked]): All participants in the letter
        required_responders (int): Minimum unique responders needed before send
        responder_count (int): Current unique responder count
        send_threshold_ratio (float | None): Effective ratio gate, or null if disabled
    """

    group: "GroupUnlinked"
    questions: list["PublicQuestion"]
    responders: list["UserUnlinked"]
    participants: list["UserUnlinked"]
    required_responders: int = 0
    responder_count: int = 0
    send_threshold_ratio: float | None = None

    @model_validator(mode="wrap")
    @classmethod
    def populate_send_threshold_progress(
        cls,
        data: Any,
        handler: ModelWrapValidatorHandler[Self],
    ) -> Self:
        """Fill send-threshold progress fields when validating from ORM letters."""
        model = handler(data)
        return _populate_letter_send_threshold_fields(model, data)


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
