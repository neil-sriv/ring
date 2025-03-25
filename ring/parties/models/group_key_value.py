from __future__ import annotations

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_json import mutable_json_type

from ring.key_value.models.model_key_value import ModelKeyValue


class GroupKeyValue(ModelKeyValue):
    """SQLAlchemy model for storing key-value pairs associated with groups.

    This model extends ModelKeyValue to provide group-specific key-value storage using
    PostgreSQL's JSONB type. It maintains a dictionary of key-value pairs that can be
    used to store arbitrary metadata for a group.

    Attributes:
        id (int): Primary key
        group_id (int): Foreign key to the associated group
        key_values (dict): JSONB dictionary storing the key-value pairs
        group (Group): Relationship to the associated group
    """

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
        """Initialize a new group key-value store.

        :param group: The group to associate with this key-value store
        :type group: Group
        """
        self.group = group
        self.key_values = dict()

    @classmethod
    def create(cls, group: Group) -> GroupKeyValue:
        """Create a new group key-value store instance.

        :param group: The group to associate with this key-value store
        :type group: Group
        :return: New group key-value store instance
        :rtype: GroupKeyValue
        """
        kv = cls(group)
        return kv
