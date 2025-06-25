from __future__ import annotations

from typing import Sequence

from casbin import Enforcer
from sqlalchemy.orm import Session

from ring.api_identifier.api_identified_model import APIIdentified
from ring.api_identifier.util import bulk_get_models, get_models
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


def bulk_can_or_inaccessible(
    db: Session,
    user: User,
    action: Action,
    resources: Sequence[APIIdentified],
) -> Sequence[APIIdentified | InaccessibleResource]:
    """Check if a user has permission to perform an action on a sequence of resources."""
    enforcer = build_stateless_enforcer(db, user.api_identifier)
    return [
        resource
        if can(db, user, action, resource, enforcer)
        else InaccessibleResource(resource)
        for resource in resources
    ]


def bulk_check(
    db: Session,
    user: User,
    action: Action,
    resources: Sequence[APIIdentified],
) -> Sequence[APIIdentified]:
    """Check if a user has permission to perform an action on a sequence of resources."""
    if any(
        isinstance(resource, InaccessibleResource)
        for resource in bulk_can_or_inaccessible(db, user, action, resources)
    ):
        raise PermissionError(
            "User does not have permission to perform action on one or more resources"
        )


def bulk_load_and_check(
    db: Session,
    user: User,
    action: Action,
    resource_api_identifiers: Sequence[str],
) -> Sequence[APIIdentified]:
    resources = bulk_get_models(db, resource_api_identifiers)
    return bulk_check(db, user, action, resources)


class InaccessibleResource:
    def __init__(
        self,
        resource: APIIdentified,
        reason: str | None = None,
    ):
        self.resource = resource
        self.reason = reason
