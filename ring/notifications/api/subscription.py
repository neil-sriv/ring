from fastapi import APIRouter

from ring.dependencies import AuthenticatedRequestDependencies
from ring.lib.logger import logger
from ring.notifications.crud.subscription import (
    create_subscription,
    get_subscriptions_for_user,
)
from ring.notifications.schemas.subscription import SubscriptionCreate
from ring.ring_pydantic.core import ResponseMessage

router = APIRouter()


@router.post("/subscription", response_model=ResponseMessage)
def post_subscription(
    subscription: SubscriptionCreate,
    req_dep: AuthenticatedRequestDependencies,
) -> ResponseMessage:
    """
    Create a subscription for the given email.
    """
    if get_subscriptions_for_user(
        req_dep.db,
        req_dep.current_user.api_identifier,
    ):
        logger.warning(
            f"User {req_dep.current_user.api_identifier} already has a subscription"
        )
        # return ResponseMessage(message="Subscription already exists")
    create_subscription(req_dep.db, subscription)
    req_dep.db.commit()

    return ResponseMessage(message="Subscription created")
