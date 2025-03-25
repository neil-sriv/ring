"""API endpoints for managing web push notification subscriptions.

This module provides endpoints for creating and managing web push notification
subscriptions, allowing users to receive notifications through their browsers.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ring.dependencies import (
    AuthenticatedRequestDependencies,
    get_request_dependencies,
)
from ring.lib.logger import logger
from ring.notifications.crud.subscription import (
    create_subscription,
    get_subscription_by_endpoint,
)
from ring.notifications.schemas.subscription import SubscriptionCreate
from ring.ring_pydantic.core import ResponseMessage

router = APIRouter()


@router.post("/subscription", response_model=ResponseMessage)
def post_subscription(
    subscription: SubscriptionCreate,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> ResponseMessage:
    """Create a new web push notification subscription.

    Creates a subscription for the authenticated user to receive web push
    notifications. If a subscription with the same endpoint already exists,
    returns a message indicating this instead of creating a duplicate.

    :param subscription: Subscription details including endpoint and keys
    :type subscription: SubscriptionCreate
    :param req_dep: Request dependencies including database session
    :type req_dep: AuthenticatedRequestDependencies
    :return: Message indicating success or existing subscription
    :rtype: ResponseMessage
    :raises HTTPException: If user is not authenticated
    """
    if get_subscription_by_endpoint(req_dep.db, subscription.endpoint):
        logger.warning(
            f"Subscription with endpoint {subscription.endpoint} already exists"
        )
        return ResponseMessage(message="Subscription already exists")
    create_subscription(req_dep.db, subscription)
    req_dep.db.commit()

    return ResponseMessage(message="Subscription created")
