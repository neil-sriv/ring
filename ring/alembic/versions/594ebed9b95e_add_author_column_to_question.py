"""add author column to question

Revision ID: 594ebed9b95e
Revises: d10224a3e726
Create Date: 2024-06-05 07:42:09.815792

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '594ebed9b95e'
down_revision: Union[str, None] = 'd10224a3e726'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('question_to_user_association')
    op.add_column('question', sa.Column('author_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'question', 'user', ['author_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'question', type_='foreignkey')
    op.drop_column('question', 'author_id')
    op.create_table('question_to_user_association',
    sa.Column('question_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['question_id'], ['question.id'], name='question_to_user_association_question_id_fkey'),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='question_to_user_association_user_id_fkey')
    )
    # ### end Alembic commands ###
