from __future__ import annotations

from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from ring.created_at import CreatedAtMixin
from ring.sqlalchemy_base import Base


class HybridSearchDocument(Base, CreatedAtMixin):
    __tablename__ = "hybrid_search_document"

    id: Mapped[int] = mapped_column(primary_key=True)

    raw_text: Mapped[str] = mapped_column(nullable=False)
    # use a computed column instead
    # text_tsv: Mapped[str] = mapped_column(TSVECTOR, nullable=False)
    text_embedding_384: Mapped[Vector] = mapped_column(
        Vector(dim=384), nullable=False
    )
    # text_embedding_1536: Mapped[Vector] = mapped_column(
    #     Vector(dimensions=1536), nullable=False
    # )

    # Add indices
    # __table_args__ = (
    # Inverted index will be added in alembic migration
    # Index("content_search_inverted_idx", text_tsv),
    # Vector index will be added in alembic migration
    # Index(
    #     "embedding_vector_idx",
    #     text_embedding_384,
    # ),
    # )

    def __init__(self, raw_text: str, text_embedding_384: Vector):
        self.raw_text = raw_text
        self.text_embedding_384 = text_embedding_384

    @classmethod
    def create(
        cls, raw_text: str, text_embedding_384: Vector
    ) -> HybridSearchDocument:
        hybrid_search_document = cls(
            raw_text=raw_text,
            text_embedding_384=text_embedding_384,
        )
        return hybrid_search_document
