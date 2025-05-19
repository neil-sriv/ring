from __future__ import annotations

from pgvector.sqlalchemy import Vector
from sqlalchemy import literal_column, select
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
    # this is a literal column that is not mapped or included in the insert/update
    text_tsv_expr_literal = literal_column("text_tsv", type_=TSVECTOR)
    text_embedding_768: Mapped[Vector] = mapped_column(
        Vector(dim=768), nullable=False
    )

    def __init__(self, raw_text: str, text_embedding_768: Vector):
        self.raw_text = raw_text
        self.text_embedding_768 = text_embedding_768

    @classmethod
    def create(
        cls, raw_text: str, text_embedding_768: Vector
    ) -> HybridSearchDocument:
        hybrid_search_document = cls(
            raw_text=raw_text,
            text_embedding_768=text_embedding_768,
        )
        return hybrid_search_document

    @property
    def text_tsv(self):
        raise AttributeError(
            "text_tsv is a computed column. Use `load_text_tsv(session)` to fetch it."
        )

    def load_text_tsv(self, session: Session) -> str:
        """Fetch the computed TSVECTOR column from the database."""
        result = session.execute(
            select(HybridSearchDocument.text_tsv_expr_literal).where(
                HybridSearchDocument.id == self.id
            )
        )
        return result.scalar_one_or_none()
