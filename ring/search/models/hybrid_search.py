from __future__ import annotations

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, UniqueConstraint, literal_column, select
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from ring.created_at import CreatedAtMixin
from ring.sqlalchemy_base import Base


class HybridSearchDocumentAssociation(Base):
    __tablename__ = "hybrid_search_document_association"

    id: Mapped[int] = mapped_column(primary_key=True)
    hybrid_search_document_id: Mapped[int] = mapped_column(
        ForeignKey(
            "hybrid_search_document.id",
            name="association_hybrid_search_document_id_fkey",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    model_api_identifier: Mapped[str] = mapped_column(nullable=False)
    model_type: Mapped[str] = mapped_column(nullable=False)

    document: Mapped["HybridSearchDocument"] = relationship(
        back_populates="associations",
    )

    __table_args__ = (
        UniqueConstraint(
            "model_api_identifier",
            "model_type",
            name="uq_model_api_identifier_model_type",
        ),
    )

    def __init__(
        self,
        model_api_identifier: str,
        model_type: str,
        hybrid_search_document: HybridSearchDocument,
    ) -> None:
        self.model_api_identifier = model_api_identifier
        self.model_type = model_type
        self.document = hybrid_search_document

    @classmethod
    def create(
        cls,
        model_api_identifier: str,
        model_type: str,
        hybrid_search_document: HybridSearchDocument,
    ) -> HybridSearchDocumentAssociation:
        association = cls(
            model_api_identifier=model_api_identifier,
            model_type=model_type,
            hybrid_search_document=hybrid_search_document,
        )
        return association


class HybridSearchDocument(Base, CreatedAtMixin):
    __tablename__ = "hybrid_search_document"

    id: Mapped[int] = mapped_column(primary_key=True)

    raw_text: Mapped[str] = mapped_column(nullable=False)
    # use a computed column instead
    # this is a literal column that is not mapped or included in the insert/update
    text_tsv_expr_literal = literal_column("text_tsv", type_=TSVECTOR)
    text_embedding_768: Mapped[Vector] = mapped_column(
        Vector(dim=768), nullable=False
    )

    associations: Mapped[list[HybridSearchDocumentAssociation]] = relationship(
        "HybridSearchDocumentAssociation", back_populates="document"
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
