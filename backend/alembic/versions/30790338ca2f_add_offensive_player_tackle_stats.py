"""add_offensive_player_tackle_stats

Revision ID: 30790338ca2f
Revises: fcb297c0eac2
Create Date: 2025-09-18 15:44:21.257079

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '30790338ca2f'
down_revision: Union[str, None] = 'fcb297c0eac2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add offensive player tackle stats to player_stats table
    op.add_column('player_stats', sa.Column('tkl', sa.Integer(), nullable=True, comment='Tackles by offensive players'))
    op.add_column('player_stats', sa.Column('tkl_solo', sa.Integer(), nullable=True, comment='Solo tackles by offensive players'))
    op.add_column('player_stats', sa.Column('tkl_ast', sa.Integer(), nullable=True, comment='Tackle assists by offensive players'))


def downgrade() -> None:
    # Remove offensive player tackle stats from player_stats table
    op.drop_column('player_stats', 'tkl_ast')
    op.drop_column('player_stats', 'tkl_solo')
    op.drop_column('player_stats', 'tkl')
