from __future__ import annotations

from enum import Enum
from typing import Sequence

from ring.api_identifier.api_identified_model import APIIdentified
from ring.authz.enforcer import get_enforcer
from ring.parties.models.user_model import User

_enforcer = get_enforcer()


class Action(Enum):
    """Action to perform on a resource."""

    READ = "read"
    WRITE = "write"


def can(user: User, action: Action, resource: APIIdentified) -> bool:
    """Check if a user has permission to perform an action on a resource."""
    return _enforcer.enforce(
        user.api_identifier, resource.api_identifier, action.value
    )


def check(user: User, action: Action, resource: APIIdentified) -> bool:
    """Check if a user has permission to perform an action on a resource."""
    if not can(user, action, resource):
        raise PermissionError(
            f"User {user.api_identifier} does not have permission to {action.value} {resource.api_identifier}"
        )


def filter_to_authorized(
    user: User, action: Action, resources: Sequence[APIIdentified]
) -> Sequence[APIIdentified]:
    """Filter a sequence of resources to only include those that the user has permission to perform an action on."""
    return [resource for resource in resources if can(user, action, resource)]
