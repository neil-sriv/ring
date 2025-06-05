"""Script to create users and groups from a JSON configuration file."""

from __future__ import annotations

import json
import os
from pprint import pp
from typing import Any

from ring.parties.crud import group as group_crud
from ring.parties.crud import user as user_crud
from ring.parties.models.group_model import Group
from ring.scripts.dependencies import (
    ScriptDependencies,
    get_script_dependencies,
    script_depends,
)


def run_script(
    dry_run: bool = True,
    deps: ScriptDependencies = script_depends(get_script_dependencies),
) -> None:
    """Create users and groups from a JSON configuration file.

    Args:
        dry_run (bool): Whether to commit changes
        deps (ScriptDependencies): Script dependencies provided by script_depends
    """
    db = deps.db
    with open(os.path.join(os.path.dirname(__file__), "users.json")) as f:
        groups_dict: list[dict[str, Any]] = json.load(f)["groups"]
    groups: list[Group] = []
    for group in groups_dict:
        # pp(group)
        admin_email = group["admin"]
        admin = user_crud.get_user_by_email(db, admin_email)
        assert admin is not None, "Admin user not found"
        g = group_crud.create_group(db, admin.api_identifier, group["name"])
        db.add(g)

        for user in group["members"]:
            if user["email"] == "neil.srivastava1@gmail.com":
                continue
            u = user_crud.create_user(
                db, user["email"], user["name"], "defaultPassword"
            )
            g.members.append(u)
            db.add(u)
        groups.append(g)

    for group in groups:
        pp(str(group))

    if dry_run:
        pp("Dry run, rolling back")
        db.rollback()
    else:
        db.commit()
