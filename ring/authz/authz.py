from __future__ import annotations

from typing import Sequence

from casbin import Enforcer
from sqlalchemy.orm import Session

from ring.api_identifier.api_identified_model import APIIdentified
from ring.authz.enforcer import (
    Action,
    build_stateless_enforcer,
    enforce_stateless,
)
from ring.parties.models.user_model import User


def can(
    db: Session,
    user: User,
    action: Action,
    resource: APIIdentified,
    enforcer: Enforcer | None = None,
) -> bool:
    """Check if a user has permission to perform an action on a resource."""
    return enforce_stateless(
        db,
        user.api_identifier,
        resource.api_identifier,
        action.value,
        enforcer,
    )


def check(
    db: Session,
    user: User,
    action: Action,
    resource: APIIdentified,
    enforcer: Enforcer | None = None,
) -> bool:
    """Check if a user has permission to perform an action on a resource."""
    if not can(db, user, action, resource, enforcer):
        raise PermissionError(
            f"User {user.api_identifier} does not have permission to {action.value} {resource.api_identifier}"
        )


def filter_to_authorized(
    db: Session,
    user: User,
    action: Action,
    resources: Sequence[APIIdentified],
) -> Sequence[APIIdentified]:
    """Filter a sequence of resources to only include those that the user has permission to perform an action on."""
    enforcer = build_stateless_enforcer(db, user.api_identifier)
    return [
        resource
        for resource in resources
        if can(db, user, action, resource, enforcer)
    ]
