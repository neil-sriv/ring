from __future__ import annotations

from pgvector.sqlalchemy import Vector
from sqlalchemy import Index
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from ring.created_at import CreatedAtMixin
from ring.sqlalchemy_base import Base


class HybridSearchDocument(Base, CreatedAtMixin):
    __tablename__ = "hybrid_search_document"

    id: Mapped[int] = mapped_column(primary_key=True)

    raw_text: Mapped[str] = mapped_column(nullable=False)
    text_tsv: Mapped[str] = mapped_column(TSVECTOR, nullable=False)
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
