from __future__ import annotations

from pgvector.sqlalchemy import Vector
from sqlalchemy import func, literal_column, select
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, Session, mapped_column

from ring.created_at import CreatedAtMixin
from ring.sqlalchemy_base import Base


class HybridSearchDocument(Base, CreatedAtMixin):
    __tablename__ = "hybrid_search_document"

    id: Mapped[int] = mapped_column(primary_key=True)

    raw_text: Mapped[str] = mapped_column(nullable=False)
    # use a computed column instead
    # _text_tsv: Mapped[str] = mapped_column(
    #     "text_tsv",
    #     TSVECTOR,
    #     nullable=False,
    #     include_in_insert=False,
    #     include_in_update=False,
    #     write_only=False,
    # )
    text_tsv_expr_literal = literal_column("text_tsv", type_=TSVECTOR)
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

    text_tsv_expr = func.to_tsvector("english", raw_text).label("text_tsv")

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

    # @property
    # def text_tsv(self) -> str:
    #     return getattr(self, "_text_tsv", None)

    @property
    def text_tsv(self):
        raise AttributeError(
            "text_tsv is a computed column. Use `load_text_tsv(session)` to fetch it."
        )

    def load_text_tsv(self, session: Session) -> str:
        """Fetches the computed column value directly from the DB."""
        result = session.execute(
            select(HybridSearchDocument.text_tsv_expr).where(
                HybridSearchDocument.id == self.id
            )
        )
        return result.scalar_one_or_none()

    # @classmethod
    # def text_tsv_column(cls):
    #     # A selectable expression for use in `select()` queries
    #     return func.to_tsvector("english", cls.raw_text).label("text_tsv")
