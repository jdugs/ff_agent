"""remove_player_projections_table

Revision ID: fcb297c0eac2
Revises: d40f68cd0259
Create Date: 2025-09-17 21:12:21.835268

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fcb297c0eac2'
down_revision: Union[str, None] = 'd40f68cd0259'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove player_projections table since we've consolidated into player_stats
    op.drop_table('player_projections')


def downgrade() -> None:
    # Recreate player_projections table
    op.create_table('player_projections',
    sa.Column('projection_id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('player_id', sa.String(length=50), nullable=False),
    sa.Column('source_id', sa.Integer(), nullable=False),
    sa.Column('week', sa.Integer(), nullable=False),
    sa.Column('year', sa.Integer(), nullable=False),
    sa.Column('league_type', sa.Enum('standard', 'ppr', 'half_ppr', 'superflex', name='league_type'), nullable=True),
    sa.Column('projected_points', sa.DECIMAL(precision=5, scale=2), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['player_id'], ['players.player_id'], ),
    sa.ForeignKeyConstraint(['source_id'], ['sources.source_id'], ),
    sa.PrimaryKeyConstraint('projection_id')
    )
