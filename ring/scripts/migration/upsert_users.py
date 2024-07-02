import json
from pprint import pp
from typing import Any, Sequence

import sqlalchemy
from ring.postgres_models.group_model import Group
from ring.postgres_models.user_model import User
from ring.sqlalchemy_base import Session
from ring.scripts.script_base import script_di
from ring.crud import user as user_crud, group as group_crud
import os


@script_di()
def run_script(db: Session, dry_run: bool = True) -> None:
    with open(os.path.join(os.path.dirname(__file__), "users.json")) as f:
        groups_dict: list[dict[str, Any]] = json.load(f)["groups"]
    groups: Sequence[Group] = db.scalars(
        sqlalchemy.select(Group).where(Group.name.in_([g["name"] for g in groups_dict]))
    ).all()
    for group in groups_dict:
        new_users: list[User] = []
        admin_email = group["admin"]
        admin = user_crud.get_user_by_email(db, admin_email)
        assert admin is not None, "Admin user not found"
        current_group = [g for g in groups if g.name == group["name"]]
        if not current_group:
            g = group_crud.create_group(db, admin.api_identifier, group["name"])
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
            print(f"\tNew user {new_user.name} added to group {g.name}")

    for group in groups:
        pp(str(group))

    if dry_run:
        pp("Dry run, rolling back")
        db.rollback()
    else:
        db.commit()
