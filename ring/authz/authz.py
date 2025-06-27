from __future__ import annotations

from typing import Optional, Sequence

from casbin import Enforcer
from fastapi import HTTPException
from sqlalchemy.orm import Session

from ring.api_identifier.api_identified_model import APIIdentified
from ring.api_identifier.util import (
    IDNotFoundException,
    bulk_get_models,
)
from ring.authz.enforcer import (
    Action,
    build_stateless_enforcer,
    enforce_stateless,
)
from ring.lib.logger import logger
from ring.parties.models.user_model import User


class AuthDeniedError(HTTPException):
    """Base exception class for authz related errors.

    Attributes:
        message (Optional[str]): Optional custom error message
    """

    def __init__(self, message: Optional[str] = None, **kwargs):
        """Initialize an AuthDeniedError.

        Args:
            message (Optional[str], optional): Custom error message. Defaults to None.
        """
        logger.error(f"AuthDeniedError: {message}", extra=kwargs)
        super().__init__(status_code=403, detail=message)


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
        action,
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
        raise AuthDeniedError(
            f"User {user.api_identifier} does not have permission to {action.value} {resource.api_identifier}",
            user=user.api_identifier,
            action=action.value,
            resource=resource.api_identifier,
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
        raise AuthDeniedError(
            "User does not have permission to perform action on one or more resources",
            user=user.api_identifier,
            action=action.value,
            resources=[r.api_identifier for r in resources],
        )
    return [
        resource
        for resource in resources
        if not isinstance(resource, InaccessibleResource)
    ]


def load_and_check(
    db: Session,
    user: User,
    action: Action,
    resource_api_identifier: str,
) -> APIIdentified:
    return bulk_load_and_check(db, user, action, [resource_api_identifier])[0]


def bulk_load_and_check(
    db: Session,
    user: User,
    action: Action,
    resource_api_identifiers: Sequence[str],
) -> Sequence[APIIdentified]:
    try:
        resources = bulk_get_models(db, resource_api_identifiers)
    except IDNotFoundException as e:
        raise AuthDeniedError(
            f"One or more resources not found or not accessible to user: {e.api_ids}",
            user=user.api_identifier,
            action=action.value,
            resources=e.api_ids,
        ) from e
    return bulk_check(db, user, action, resources)


class InaccessibleResource:
    def __init__(
        self,
        resource: APIIdentified,
        reason: str | None = None,
    ):
        self.resource = resource
        self.reason = reason
