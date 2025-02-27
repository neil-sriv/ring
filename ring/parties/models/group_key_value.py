from __future__ import annotations

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_json import mutable_json_type

from ring.key_value.models.model_key_value import ModelKeyValue


class GroupKeyValue(ModelKeyValue):
    """Key-value storage for groups."""

    __tablename__ = "group_key_value"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("group.id"), index=True)
    key_values: Mapped[dict] = mapped_column(
        mutable_json_type(dbtype=JSONB, nested=True),
        default=dict,
        nullable=False,
    )
    group = relationship("Group", back_populates="key_values")

    __mapper_args__ = {"polymorphic_identity": "group", "concrete": True}

    def __init__(self, group: Group) -> None:
        self.group = group
        self.key_values = dict()

    @classmethod
    def create(cls, group: Group) -> GroupKeyValue:
        kv = cls(group)
        return kv
