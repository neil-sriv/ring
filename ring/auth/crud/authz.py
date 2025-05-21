from __future__ import annotations

from sqlalchemy.orm import Session

from ring.api_identifier.api_identified_model import APIIdentified
from ring.parties.models.user_model import User


def filter_to_readable(
    db: Session, model: APIIdentified, user: User
) -> APIIdentified:
    return model
