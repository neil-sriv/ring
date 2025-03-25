from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Sequence

from sqlalchemy import select

from ring.api_identifier import util as api_identifier_crud
from ring.letters.constants import DEFAULT_QUESTIONS
from ring.letters.crud.default_question import replace_default_questions
from ring.letters.models.letter_model import Letter
from ring.parties.models.group_model import Group
from ring.parties.models.user_model import User
from ring.tasks.crud import (
    schedule as schedule_crud,
)
from ring.tasks.models.task_model import TaskType

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_groups(
    db: Session, user_api_id: str, skip: int = 0, limit: int = 100
) -> Sequence[Group]:
    """Get all groups that a user is a member of.

    :param db: Database session
    :type db: Session
    :param user_api_id: API identifier of the user
    :type user_api_id: str
    :param skip: Number of records to skip, defaults to 0
    :type skip: int, optional
    :param limit: Maximum number of records to return, defaults to 100
    :type limit: int, optional
    :return: List of groups
    :rtype: Sequence[Group]
    """
    user = api_identifier_crud.get_model(db, User, api_id=user_api_id)
    return db.scalars(
        select(Group)
        .filter(
            Group.members.contains(user),
        )
        .offset(skip)
        .limit(limit)
    ).all()


def create_group(db: Session, admin_api_id: str, name: str) -> Group:
    """Create a new group with the specified admin and name.

    :param db: Database session
    :type db: Session
    :param admin_api_id: API identifier of the admin user
    :type admin_api_id: str
    :param name: Name of the group
    :type name: str
    :return: Created group
    :rtype: Group
    """
    admin_user = api_identifier_crud.get_model(
        db,
        User,
        api_id=admin_api_id,
    )
    db_group = Group.create(name, admin_user)
    db.add(db_group)
    replace_default_questions(db, db_group, DEFAULT_QUESTIONS)
    return db_group


def update_cycle_length(db: Session, group: Group, cycle_length: int) -> Group:
    """Update the cycle length of a group.

    :param db: Database session
    :type db: Session
    :param group: Group to update
    :type group: Group
    :param cycle_length: New cycle length in days
    :type cycle_length: int
    :return: Updated group
    :rtype: Group
    """
    group.cycle_length = cycle_length
    return group


def get_cycle_length(db: Session, group: Group) -> int:
    """Get the cycle length of a group.

    :param db: Database session
    :type db: Session
    :param group: Group to query
    :type group: Group
    :return: Cycle length in days
    :rtype: int
    """
    return group.cycle_length


def add_member(db: Session, group_api_id: str, user_api_id: str) -> Group:
    """Add a user to a group and its active letters.

    :param db: Database session
    :type db: Session
    :param group_api_id: API identifier of the group
    :type group_api_id: str
    :param user_api_id: API identifier of the user to add
    :type user_api_id: str
    :return: Updated group
    :rtype: Group
    """
    db_group = api_identifier_crud.get_model(db, Group, api_id=group_api_id)
    db_user = api_identifier_crud.get_model(db, User, api_id=user_api_id)
    db_group.members.append(db_user)
    if db_group.in_progress_letter:
        db_group.in_progress_letter.participants.append(db_user)
    if db_group.upcoming_letter:
        db_group.upcoming_letter.participants.append(db_user)
    return db_group


def remove_member(db: Session, group_api_id: str, user_api_id: str) -> Group:
    """Remove a user from a group.

    :param db: Database session
    :type db: Session
    :param group_api_id: API identifier of the group
    :type group_api_id: str
    :param user_api_id: API identifier of the user to remove
    :type user_api_id: str
    :return: Updated group
    :rtype: Group
    :raises ValueError: If the user is not a member of the group
    """
    db_group = api_identifier_crud.get_model(db, Group, api_id=group_api_id)
    db_user = api_identifier_crud.get_model(db, User, api_id=user_api_id)
    if db_user not in db_group.members:
        raise ValueError(
            f"User {user_api_id} is not a member of group {group_api_id}"
        )
    db_group.members.remove(db_user)
    return db_group


def get_letter_by_api_id(group: Group, api_id: str) -> Letter:
    """Get a letter from a group by its API identifier.

    :param group: Group containing the letter
    :type group: Group
    :param api_id: API identifier of the letter
    :type api_id: str
    :return: Found letter
    :rtype: Letter
    :raises ValueError: If no letter with the given API ID is found
    """
    letter = next(
        filter(
            lambda letter: letter.api_identifier == api_id,
            group.letters,
        ),
        None,
    )
    if not letter:
        raise ValueError(f"Could not find letter with api_id {api_id}")
    return letter


def schedule_send(
    db: Session, group_api_id: str, letter_api_id: str, send_at: datetime
) -> Group:
    """Schedule a letter to be sent at a specific time.

    :param db: Database session
    :type db: Session
    :param group_api_id: API identifier of the group
    :type group_api_id: str
    :param letter_api_id: API identifier of the letter
    :type letter_api_id: str
    :param send_at: When to send the letter
    :type send_at: datetime
    :return: Updated group
    :rtype: Group
    """
    db_group = api_identifier_crud.get_model(db, Group, api_id=group_api_id)
    db_letter = get_letter_by_api_id(db_group, letter_api_id)
    schedule_crud.register_task(
        db,
        db_group.schedule,
        TaskType.SEND_EMAIL,
        send_at,
        {"letter_api_id": db_letter.api_identifier},
    )
    return db_group


def add_members(db: Session, group: Group, members: Sequence[User]) -> None:
    """Add multiple users to a group.

    :param db: Database session
    :type db: Session
    :param group: Group to add members to
    :type group: Group
    :param members: Users to add
    :type members: Sequence[User]
    """
    for member in members:
        if member not in group.members:
            group.members.append(member)
