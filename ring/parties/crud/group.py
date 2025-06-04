"""CRUD operations for group management.

This module provides functions for managing groups in the database, including
creation, member management, and letter scheduling.
"""

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
from ring.search.crud.hybrid_search import (
    SearchableType,
    create_hybrid_search_document,
)
from ring.search.models.hybrid_search import HybridSearchDocument
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

    Args:
        db (Session): Database session
        user_api_id (str): API identifier of the user
        skip (int, optional): Number of records to skip. Defaults to 0.
        limit (int, optional): Maximum number of records to return. Defaults to 100.

    Returns:
        Sequence[Group]: List of groups
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

    Args:
        db (Session): Database session
        admin_api_id (str): API identifier of the admin user
        name (str): Name of the group

    Returns:
        Group: Created group
    """
    admin_user = api_identifier_crud.get_model(
        db,
        User,
        api_id=admin_api_id,
    )
    db_group = Group.create(name, admin_user)
    db.add(db_group)
    db.add(create_group_search_document(db, db_group))
    replace_default_questions(db, db_group, DEFAULT_QUESTIONS)
    return db_group


def update_cycle_length(db: Session, group: Group, cycle_length: int) -> Group:
    """Update the cycle length of a group.

    Args:
        db (Session): Database session
        group (Group): Group to update
        cycle_length (int): New cycle length in days

    Returns:
        Group: Updated group
    """
    group.cycle_length = cycle_length
    return group


def get_cycle_length(db: Session, group: Group) -> int:
    """Get the cycle length of a group.

    Args:
        db (Session): Database session
        group (Group): Group to query

    Returns:
        int: Cycle length in days
    """
    return group.cycle_length


def add_member(db: Session, group_api_id: str, user_api_id: str) -> Group:
    """Add a user to a group and its active letters.

    Args:
        db (Session): Database session
        group_api_id (str): API identifier of the group
        user_api_id (str): API identifier of the user to add

    Returns:
        Group: Updated group
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

    Args:
        db (Session): Database session
        group_api_id (str): API identifier of the group
        user_api_id (str): API identifier of the user to remove

    Returns:
        Group: Updated group

    Raises:
        ValueError: If the user is not a member of the group
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

    Args:
        group (Group): Group containing the letter
        api_id (str): API identifier of the letter

    Returns:
        Letter: Found letter

    Raises:
        ValueError: If no letter with the given API ID is found
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

    Args:
        db (Session): Database session
        group_api_id (str): API identifier of the group
        letter_api_id (str): API identifier of the letter
        send_at (datetime): When to send the letter

    Returns:
        Group: Updated group
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

    Args:
        db (Session): Database session
        group (Group): Group to add members to
        members (Sequence[User]): Users to add to the group
    """
    group.members.extend(members)
    if group.in_progress_letter:
        group.in_progress_letter.participants.extend(members)
    if group.upcoming_letter:
        group.upcoming_letter.participants.extend(members)


def create_group_search_document(
    db: Session, group: Group
) -> HybridSearchDocument:
    """Create a search document for a group.

    Args:
        db (Session): Database session
        group (Group): Group to create a search document for

    Returns:
        HybridSearchDocument: Search document for the group
    """
    member_names = " ".join(member.name for member in group.members)
    key_values = " ".join(
        f"{key}: {value}" for key, value in group.key_values.items()
    )
    raw_text = f"{group.name} {member_names} {key_values}"
    return create_hybrid_search_document(
        db, raw_text, group.api_identifier, SearchableType.GROUP
    )
