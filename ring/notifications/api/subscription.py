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
    """
    Create a subscription for the given email.
    """
    if get_subscription_by_endpoint(req_dep.db, subscription.endpoint):
        logger.warning(
            f"Subscription with endpoint {subscription.endpoint} already exists"
        )
        return ResponseMessage(message="Subscription already exists")
    create_subscription(req_dep.db, subscription)
    req_dep.db.commit()

    return ResponseMessage(message="Subscription created")
