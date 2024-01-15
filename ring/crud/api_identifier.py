from __future__ import annotations
from typing import TYPE_CHECKING, Optional, TypeVar


if TYPE_CHECKING:
    from sqlalchemy.orm import Session

APIIdentifiedType = TypeVar("APIIdentifiedType")


def get_model(
    db: Session, model_cls: type[APIIdentifiedType], api_id: str
) -> Optional[APIIdentifiedType]:
    return db.query(model_cls).filter(model_cls.api_identifier == api_id).one_or_none()
