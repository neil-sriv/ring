from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from loguru import logger
from sqlalchemy import (
    BLOB,
    Constraint,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    Sequence,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from ring.api_identifier.api_identified_model import APIIdentified, APIPrefix
from ring.api_identifier.util import register_api_class
from ring.created_at import CreatedAtMixin
from ring.notebook.schemas.document import DocumentResponse
from ring.parties.models.group_model import Group
from ring.ring_pydantic.pydantic_model import PydanticModel
from ring.sqlalchemy_base import Base

if TYPE_CHECKING:
    from ring.parties.models.user_model import User


@register_api_class(APIPrefix.DOCUMENT)
class Document(Base, APIIdentified, CreatedAtMixin, PydanticModel):
    __tablename__ = "documents"

    API_ID_PREFIX = APIPrefix.DOCUMENT
    PYDANTIC_MODEL = DocumentResponse

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    content: Mapped[bytes] = mapped_column(BLOB(), nullable=False)
    latest_snapshot_version: Mapped[int] = mapped_column(nullable=False)

    edits: Mapped[list["DocumentEdit"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )

    group_id: Mapped[int] = mapped_column(ForeignKey("group.id"))
    group: Mapped["Group"] = relationship()

    def __init__(
        self,
        name: str,
        content: bytes,
        latest_snapshot_version: int,
        group: Group,
    ):
        APIIdentified.__init__(self)
        self.name = name
        self.content = content
        self.latest_snapshot_version = latest_snapshot_version
        self.group = group

    @classmethod
    def create(cls, name: str, content: str, group: Group):
        # Convert string content to bytes for storage
        content_bytes = (
            content.encode("utf-8") if isinstance(content, str) else content
        )
        return cls(
            name=name,
            content=content_bytes,
            latest_snapshot_version=0,
            group=group,
        )


class DocumentEdit(Base, CreatedAtMixin):
    __tablename__ = "document_edits"

    id: Mapped[int] = mapped_column(primary_key=True)
    delta: Mapped[bytes] = mapped_column(BLOB(), nullable=False)
    version_seq = Sequence("document_edit_version_seq")
    version: Mapped[int] = mapped_column(
        Integer,
        version_seq,
        nullable=False,
        server_default=version_seq.next_value(),
    )

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id"), nullable=False
    )
    document: Mapped["Document"] = relationship(back_populates="edits")

    # Nullable: CRDT sync updates are document-level and carry no single author.
    author_id: Mapped[int | None] = mapped_column(
        ForeignKey("user.id"), nullable=True
    )
    author: Mapped["User | None"] = relationship()

    @declared_attr  # type: ignore
    def __table_args__(cls) -> tuple[Constraint]:
        """Define table constraints.

        Returns:
            tuple[Constraint]: Tuple of table constraints
        """
        return (
            UniqueConstraint(
                "document_id",
                "version",
                name="unique_document_edit_version",
            ),
        )

    def __init__(
        self,
        document: Document,
        delta: bytes,
        author: User | None = None,
    ):
        self.document = document
        self.delta = delta
        self.author = author
