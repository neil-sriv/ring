"""add search association filter metadata

Revision ID: f36847c5bb55
Revises: 45bf29f5dbb8
Create Date: 2026-06-23 08:09:02.472390

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f36847c5bb55"
down_revision: Union[str, None] = "45bf29f5dbb8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE hybrid_search_document_association
        ADD COLUMN IF NOT EXISTS group_api_id VARCHAR
        """
    )
    op.execute(
        """
        ALTER TABLE hybrid_search_document_association
        ADD COLUMN IF NOT EXISTS participant_api_id VARCHAR
        """
    )
    op.execute(
        """
        ALTER TABLE hybrid_search_document_association
        ADD COLUMN IF NOT EXISTS entity_created_at TIMESTAMPTZ
        """
    )

    op.execute(
        """
        UPDATE hybrid_search_document_association AS a
        SET entity_created_at = r.created_at
        FROM response AS r
        WHERE a.model_type = 'response'
          AND a.model_api_identifier = r.api_identifier
        """
    )
    op.execute(
        """
        UPDATE hybrid_search_document_association AS a
        SET entity_created_at = q.created_at
        FROM question AS q
        WHERE a.model_type = 'question'
          AND a.model_api_identifier = q.api_identifier
        """
    )
    op.execute(
        """
        UPDATE hybrid_search_document_association AS a
        SET entity_created_at = l.created_at
        FROM letter AS l
        WHERE a.model_type = 'letter'
          AND a.model_api_identifier = l.api_identifier
        """
    )
    op.execute(
        """
        UPDATE hybrid_search_document_association AS a
        SET entity_created_at = g.created_at
        FROM "group" AS g
        WHERE a.model_type = 'group'
          AND a.model_api_identifier = g.api_identifier
        """
    )
    op.execute(
        """
        UPDATE hybrid_search_document_association AS a
        SET entity_created_at = u.created_at
        FROM "user" AS u
        WHERE a.model_type = 'user'
          AND a.model_api_identifier = u.api_identifier
        """
    )
    op.execute(
        """
        UPDATE hybrid_search_document_association AS a
        SET entity_created_at = d.created_at
        FROM hybrid_search_document AS d
        WHERE a.hybrid_search_document_id = d.id
          AND a.entity_created_at IS NULL
        """
    )

    op.execute(
        """
        UPDATE hybrid_search_document_association AS a
        SET group_api_id = g.api_identifier
        FROM response AS r
        JOIN question AS q ON r.question_id = q.id
        JOIN letter AS l ON q.letter_id = l.id
        JOIN "group" AS g ON l.group_id = g.id
        WHERE a.model_type = 'response'
          AND a.model_api_identifier = r.api_identifier
        """
    )
    op.execute(
        """
        UPDATE hybrid_search_document_association AS a
        SET group_api_id = g.api_identifier
        FROM question AS q
        JOIN letter AS l ON q.letter_id = l.id
        JOIN "group" AS g ON l.group_id = g.id
        WHERE a.model_type = 'question'
          AND a.model_api_identifier = q.api_identifier
        """
    )
    op.execute(
        """
        UPDATE hybrid_search_document_association AS a
        SET group_api_id = g.api_identifier
        FROM letter AS l
        JOIN "group" AS g ON l.group_id = g.id
        WHERE a.model_type = 'letter'
          AND a.model_api_identifier = l.api_identifier
        """
    )
    op.execute(
        """
        UPDATE hybrid_search_document_association AS a
        SET group_api_id = g.api_identifier
        FROM "group" AS g
        WHERE a.model_type = 'group'
          AND a.model_api_identifier = g.api_identifier
        """
    )
    op.execute(
        """
        UPDATE hybrid_search_document_association AS a
        SET participant_api_id = u.api_identifier
        FROM response AS r
        JOIN "user" AS u ON r.participant_id = u.id
        WHERE a.model_type = 'response'
          AND a.model_api_identifier = r.api_identifier
        """
    )

    op.alter_column(
        "hybrid_search_document_association",
        "entity_created_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )

    op.create_index(
        op.f("ix_hybrid_search_document_association_entity_created_at"),
        "hybrid_search_document_association",
        ["entity_created_at"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        op.f("ix_hybrid_search_document_association_group_api_id"),
        "hybrid_search_document_association",
        ["group_api_id"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        op.f("ix_hybrid_search_document_association_participant_api_id"),
        "hybrid_search_document_association",
        ["participant_api_id"],
        unique=False,
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_hybrid_search_document_association_participant_api_id"),
        table_name="hybrid_search_document_association",
    )
    op.drop_index(
        op.f("ix_hybrid_search_document_association_group_api_id"),
        table_name="hybrid_search_document_association",
    )
    op.drop_index(
        op.f("ix_hybrid_search_document_association_entity_created_at"),
        table_name="hybrid_search_document_association",
    )
    op.drop_column("hybrid_search_document_association", "entity_created_at")
    op.drop_column("hybrid_search_document_association", "participant_api_id")
    op.drop_column("hybrid_search_document_association", "group_api_id")
