"""Migration script to upsert users and groups from a JSON configuration file.

This script reads a users.json file containing group and user configurations,
then creates or updates groups and their members in the Ring database. For each group,
it ensures the admin user exists and creates any new member users that don't already exist.
"""

from __future__ import annotations

import json
import os
from pprint import pp
from typing import Any, Sequence

import sqlalchemy

from ring.lib.logger import logger
from ring.parties.crud import group as group_crud
from ring.parties.crud import user as user_crud
from ring.parties.models.group_model import Group
from ring.parties.models.user_model import User
from ring.scripts.dependencies import (
    ScriptDependencies,
    get_script_dependencies,
    script_depends,
)


def run_script(
    dry_run: bool = True,
    deps: ScriptDependencies = script_depends(get_script_dependencies),
) -> None:
    """Upsert users and groups from a JSON configuration file.

    This function reads a users.json file from the same directory as this script,
    which should contain a list of groups with their admins and members. For each group:
    1. Verifies the admin user exists
    2. Creates the group if it doesn't exist
    3. Creates any new member users that don't already exist in the group
    4. Adds the new users to the group

    Args:
        dry_run (bool, optional): If True, rolls back all changes. Defaults to True.
        deps (ScriptDependencies): Script dependencies provided by script_depends

    Raises:
        AssertionError: If an admin user specified in the JSON file is not found
    """
    db = deps.db
    with open(os.path.join(os.path.dirname(__file__), "users.json")) as f:
        groups_dict: list[dict[str, Any]] = json.load(f)["groups"]
    groups: Sequence[Group] = db.scalars(
        sqlalchemy.select(Group).where(
            Group.name.in_([g["name"] for g in groups_dict])
        )
    ).all()
    for group in groups_dict:
        new_users: list[User] = []
        admin_email = group["admin"]
        admin = user_crud.get_user_by_email(db, admin_email)
        assert admin is not None, "Admin user not found"
        current_group = [g for g in groups if g.name == group["name"]]
        if not current_group:
            g = group_crud.create_group(
                db, admin.api_identifier, group["name"]
            )
            db.add(g)
            db.flush()
            pp(f"New group {g.name} created with admin {admin.name}")
        else:
            g = current_group[0]
            pp(f"Updating existing group {g.name} with admin {admin.name}")
        members = g.members

        for user in group["members"]:
            if user["email"] in [m.email for m in members]:
                continue
            u = user_crud.create_user(
                db, user["email"], user["name"], "defaultPassword"
            )
            new_users.append(u)
            g.members.append(u)
            db.add(u)
        db.flush()
        for new_user in new_users:
            logger.info(
                "New user {} added to group {}".format(new_user.name, g.name)
            )

    for group in groups:
        pp(str(group))

    if dry_run:
        pp("Dry run, rolling back")
        db.rollback()
    else:
        db.commit()
