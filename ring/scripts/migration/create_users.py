import json
from pprint import pp
from typing import Any
from ring.postgres_models.group_model import Group
from ring.sqlalchemy_base import Session
from ring.scripts.script_base import script_di
from ring.crud import group as group_crud, user as user_crud
import os


@script_di()
def run_script(db: Session, dry_run: bool = True) -> None:
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
