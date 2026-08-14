"""Main router configuration for Ring's API.

This module configures the main API router and includes all sub-routers for
different parts of the application. It organizes routes by feature area and
provides appropriate URL prefixes and tags for API documentation.
"""

from __future__ import annotations

from fastapi import APIRouter

from ring.auth.api import authn
from ring.fastapp.api import version
from ring.letters.api import letter, question, response
from ring.llm.api import completion
from ring.notebook.api import document
from ring.notifications.api import subscription
from ring.parties.api import group, group_key_value, invite, user
from ring.search.api import search
from ring.sharing.api import share_link
from ring.tasks.api import schedule
from ring.unfurl.api import unfurl

router = APIRouter()

# Authentication routes
router.include_router(authn.router, tags=["login"])
router.include_router(version.router, tags=["meta"])
router.include_router(unfurl.router, tags=["meta"])

# User and group management routes
router.include_router(user.router, prefix="/parties", tags=["parties"])
router.include_router(group.router, prefix="/parties", tags=["parties"])
router.include_router(
    group_key_value.router, prefix="/parties", tags=["parties"]
)

# Letter and content routes
router.include_router(letter.router, prefix="/letters", tags=["letters"])
router.include_router(schedule.router, prefix="/schedule", tags=["schedule"])
router.include_router(question.router, prefix="/questions", tags=["questions"])
router.include_router(response.router, prefix="/responses", tags=["responses"])

# Invitation and notification routes
router.include_router(invite.router, prefix="/invites", tags=["invites"])
router.include_router(
    subscription.router,
    prefix="/notifications",
    tags=["notifications"],
)

router.include_router(completion.router, prefix="/llm", tags=["llm"])

router.include_router(search.router, prefix="/search", tags=["search"])

router.include_router(share_link.router, prefix="/shares", tags=["shares"])

router.include_router(
    document.websocket_router, prefix="/ws/notebook", tags=["notebook"]
)
router.include_router(document.router, prefix="/notebook", tags=["notebook"])


@router.get("/")
async def root() -> dict[str, str]:
    """Root endpoint for health checks.

    Returns:
        dict[str, str]: Simple health check response
    """
    return {"message": "Hello World!"}


@router.get("/hello")
async def hello() -> dict[str, str]:
    """Test endpoint.

    Returns:
        dict[str, str]: Simple test response
    """
    return {"message": "Hello World!"}
