"""Permission checks and the baseline grants supplied by group roles.

Call sites ask whether a user holds a permission on a resource. They do not
read ``group.admin``. Group membership writes the baseline rows: the admin
holds ``admin`` on the group, other members hold ``member``. ``admin`` on a
group satisfies ``admin`` and ``member`` on that group's loops. An explicit
``admin`` grant on one loop does not extend to the group or to other loops.
"""

from __future__ import annotations

from typing import Iterable

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, object_session
from sqlalchemy.orm.attributes import PASSIVE_NO_INITIALIZE, get_history

from ring.api_identifier.api_identified_model import APIIdentified
from ring.authz.permission_grant import Permission, PermissionGrant
from ring.letters.models.letter_model import Letter
from ring.parties.models.group_model import Group
from ring.parties.models.user_model import User

_GRANT_CACHE = "permission_grant_cache"
_SYNC_REGISTERED = False


def subject_api_ids(user: User) -> list[str]:
    """Subjects whose grants apply to this user.

    A closure over genesis IdP nested groups can append group subjects here.
    """
    return [user.api_identifier]


def resource_and_ancestors(resource: APIIdentified) -> list[str]:
    """The resource and the parents a grant on an ancestor should cover.

    A closure table replaces this walk. Letter grants cover that letter;
    group grants cover the group and its letters and questions.
    """
    ids = [resource.api_identifier]
    letter = getattr(resource, "letter", None)
    parent = getattr(letter, "group", None) if letter is not None else None
    if letter is not None:
        ids.append(letter.api_identifier)
    else:
        parent = getattr(resource, "group", None)
    parent_api_id = getattr(parent, "api_identifier", None)
    if parent_api_id:
        ids.append(parent_api_id)
    return list(dict.fromkeys(ids))


def _satisfying(permission: Permission) -> set[str]:
    if permission is Permission.MEMBER:
        return {Permission.ADMIN.value, Permission.MEMBER.value}
    return {permission.value}


def clear_grant_cache(db: Session) -> None:
    db.info.pop(_GRANT_CACHE, None)


def _grants_for_subject(
    db: Session, subject_api_id: str
) -> set[tuple[str, str]]:
    cache: dict[str, set[tuple[str, str]]] = db.info.setdefault(
        _GRANT_CACHE, {}
    )
    cached = cache.get(subject_api_id)
    if cached is not None:
        return cached
    rows = db.execute(
        select(
            PermissionGrant.resource_api_id,
            PermissionGrant.permission,
        ).where(PermissionGrant.subject_api_id == subject_api_id)
    ).all()
    grants = {
        (resource_api_id, permission) for resource_api_id, permission in rows
    }
    cache[subject_api_id] = grants
    return grants


def holds_permission(
    db: Session,
    user: User,
    permission: Permission,
    resource: APIIdentified,
) -> bool:
    """Return whether ``user`` holds ``permission`` on ``resource``."""
    allowed = _satisfying(permission)
    ancestors = set(resource_and_ancestors(resource))
    for subject_api_id in subject_api_ids(user):
        for resource_api_id, granted in _grants_for_subject(
            db, subject_api_id
        ):
            if resource_api_id in ancestors and granted in allowed:
                return True
    return False


def require_permission(
    db: Session,
    user: User,
    permission: Permission,
    resource: APIIdentified,
    *,
    action: str,
) -> None:
    """Raise 403 when ``user`` does not hold ``permission`` on ``resource``."""
    if holds_permission(db, user, permission, resource):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"Not authorized to {action}",
    )


def grant_permission(
    db: Session,
    subject_api_id: str,
    resource_api_id: str,
    permission: Permission,
) -> PermissionGrant:
    """Ensure one grant row exists. Existing rows are left in place."""
    with db.no_autoflush:
        existing = db.scalar(
            select(PermissionGrant).where(
                PermissionGrant.subject_api_id == subject_api_id,
                PermissionGrant.resource_api_id == resource_api_id,
                PermissionGrant.permission == permission.value,
            )
        )
        pending = [
            row
            for row in db.new
            if isinstance(row, PermissionGrant)
            and row.subject_api_id == subject_api_id
            and row.resource_api_id == resource_api_id
            and row.permission == permission.value
        ]
    if existing is not None:
        return existing
    if pending:
        return pending[0]
    grant = PermissionGrant(
        subject_api_id=subject_api_id,
        resource_api_id=resource_api_id,
        permission=permission.value,
    )
    db.add(grant)
    clear_grant_cache(db)
    return grant


def _grants_on_resource(
    db: Session, resource_api_id: str
) -> list[PermissionGrant]:
    with db.no_autoflush:
        rows = list(
            db.scalars(
                select(PermissionGrant).where(
                    PermissionGrant.resource_api_id == resource_api_id
                )
            ).all()
        )
        pending = [
            row
            for row in db.new
            if isinstance(row, PermissionGrant)
            and row.resource_api_id == resource_api_id
            and row not in rows
        ]
    deleted = set(db.deleted)
    return [row for row in rows + pending if row not in deleted]


def _revoke_loop_grants(
    db: Session, group: Group, subject_api_ids_to_revoke: Iterable[str]
) -> None:
    subjects = set(subject_api_ids_to_revoke)
    if not subjects or group.id is None:
        return
    loop_api_ids = list(
        db.scalars(
            select(Letter.api_identifier).where(Letter.group_id == group.id)
        ).all()
    )
    if not loop_api_ids:
        return
    db.execute(
        delete(PermissionGrant).where(
            PermissionGrant.subject_api_id.in_(subjects),
            PermissionGrant.resource_api_id.in_(loop_api_ids),
        ),
        execution_options={"synchronize_session": "fetch"},
    )
    for row in list(db.new):
        if (
            isinstance(row, PermissionGrant)
            and row.subject_api_id in subjects
            and row.resource_api_id in loop_api_ids
        ):
            db.expunge(row)
    clear_grant_cache(db)


def sync_group_baseline_grants(db: Session, group: Group) -> None:
    """Rewrite this group's role grants to match its admin and members.

    ``admin`` is stored for the group admin and ``member`` for everyone else.
    Removing a member also drops their grants on the group's loops.
    """
    admin = group.admin
    if admin is None:
        return
    members = list(group.members)
    desired: dict[str, str] = {
        member.api_identifier: Permission.MEMBER.value for member in members
    }
    desired[admin.api_identifier] = Permission.ADMIN.value

    existing = _grants_on_resource(db, group.api_identifier)
    by_subject: dict[str, list[PermissionGrant]] = {}
    for grant in existing:
        by_subject.setdefault(grant.subject_api_id, []).append(grant)

    removed = set(by_subject) - set(desired)
    if removed:
        _revoke_loop_grants(db, group, removed)
        for subject_api_id in removed:
            for grant in by_subject[subject_api_id]:
                db.delete(grant)

    for subject_api_id, permission in desired.items():
        rows = by_subject.get(subject_api_id, [])
        keeper = next(
            (row for row in rows if row.permission == permission), None
        )
        if keeper is None and rows:
            keeper = rows[0]
            keeper.permission = permission
        elif keeper is None:
            db.add(
                PermissionGrant(
                    subject_api_id=subject_api_id,
                    resource_api_id=group.api_identifier,
                    permission=permission,
                )
            )
        for extra in rows:
            if extra is not keeper:
                db.delete(extra)
    clear_grant_cache(db)


def _groups_pending_baseline_sync(db: Session) -> list[Group]:
    groups: list[Group] = []
    seen: set[int] = set()

    def consider(obj: object, *, force: bool) -> None:
        if not isinstance(obj, Group) or id(obj) in seen:
            return
        if object_session(obj) is not db:
            return
        if not force:
            members_hist = get_history(obj, "members", PASSIVE_NO_INITIALIZE)
            admin_hist = get_history(obj, "_admin", PASSIVE_NO_INITIALIZE)
            if not members_hist.has_changes() and not admin_hist.has_changes():
                return
        seen.add(id(obj))
        groups.append(obj)

    for obj in db.new:
        consider(obj, force=True)
    for obj in db.dirty:
        consider(obj, force=False)
    for obj in db.identity_map.values():
        consider(obj, force=False)
    return groups


def register_grant_sync() -> None:
    """Keep baseline grants aligned when a group flush changes roles."""
    global _SYNC_REGISTERED
    if _SYNC_REGISTERED:
        return
    from sqlalchemy import event

    @event.listens_for(Session, "before_flush")
    def _sync_baseline_grants(
        db: Session,
        flush_context: object,
        instances: object,
    ) -> None:
        if db.info.get("permission_grant_syncing"):
            return
        db.info["permission_grant_syncing"] = True
        try:
            with db.no_autoflush:
                for group in _groups_pending_baseline_sync(db):
                    sync_group_baseline_grants(db, group)
        finally:
            db.info.pop("permission_grant_syncing", None)

    _SYNC_REGISTERED = True
