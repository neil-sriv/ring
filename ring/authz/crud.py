from __future__ import annotations

from casbin import Enforcer, util

from ring.api_identifier.api_identified_model import APIIdentified
from ring.parties.models.user_model import User


def is_descendant(child: APIIdentified, parent: APIIdentified) -> bool:
    """Check if a child is a descendant of a parent."""
    pass


def is_author(user: User, model: APIIdentified) -> bool:
    """Check if a user is the author of a model."""
    pass
