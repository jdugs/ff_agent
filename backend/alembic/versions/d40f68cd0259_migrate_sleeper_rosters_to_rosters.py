"""migrate_sleeper_rosters_to_rosters

Revision ID: d40f68cd0259
Revises: 9551729d3c90
Create Date: 2025-09-17 21:01:15.823375

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd40f68cd0259'
down_revision: Union[str, None] = '9551729d3c90'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Migrate sleeper_rosters to rosters table structure

    # Create new rosters table
    op.create_table('rosters',
    sa.Column('roster_id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('platform_roster_id', sa.Integer(), nullable=False),
    sa.Column('league_id', sa.String(length=50), nullable=False),
    sa.Column('owner_id', sa.String(length=50), nullable=True),
    sa.Column('player_ids', sa.JSON(), nullable=True),
    sa.Column('starters', sa.JSON(), nullable=True),
    sa.Column('reserve', sa.JSON(), nullable=True),
    sa.Column('taxi', sa.JSON(), nullable=True),
    sa.Column('settings', sa.JSON(), nullable=True),
    sa.Column('wins', sa.Integer(), nullable=True),
    sa.Column('losses', sa.Integer(), nullable=True),
    sa.Column('ties', sa.Integer(), nullable=True),
    sa.Column('fpts', sa.DECIMAL(precision=6, scale=2), nullable=True),
    sa.Column('fpts_against', sa.DECIMAL(precision=6, scale=2), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('roster_id'),
    sa.ForeignKeyConstraint(['league_id'], ['leagues.league_id'], )
    )
    op.create_index(op.f('ix_rosters_league_id'), 'rosters', ['league_id'], unique=False)
    op.create_index(op.f('ix_rosters_platform_roster_id'), 'rosters', ['platform_roster_id'], unique=False)
    op.create_index('ix_rosters_league_platform', 'rosters', ['league_id', 'platform_roster_id'], unique=False)
    op.create_index('ix_rosters_owner_league', 'rosters', ['owner_id', 'league_id'], unique=False)

    # Migrate data from sleeper_rosters to rosters
    op.execute("""
        INSERT INTO rosters
        (platform_roster_id, league_id, owner_id, player_ids, starters, reserve, taxi, settings,
         wins, losses, ties, fpts, fpts_against, created_at, updated_at)
        SELECT
            roster_id, league_id, owner_id, player_ids, starters, reserve, taxi, settings,
            wins, losses, ties, fpts, fpts_against, created_at, updated_at
        FROM sleeper_rosters
    """)

    # Drop the old sleeper_rosters table
    op.drop_table('sleeper_rosters')


def downgrade() -> None:
    # Reverse the rosters migration

    # Recreate sleeper_rosters table
    op.create_table('sleeper_rosters',
    sa.Column('roster_id', sa.Integer(), nullable=False),
    sa.Column('league_id', sa.String(length=50), nullable=False),
    sa.Column('owner_id', sa.String(length=50), nullable=True),
    sa.Column('player_ids', sa.JSON(), nullable=True),
    sa.Column('starters', sa.JSON(), nullable=True),
    sa.Column('reserve', sa.JSON(), nullable=True),
    sa.Column('taxi', sa.JSON(), nullable=True),
    sa.Column('settings', sa.JSON(), nullable=True),
    sa.Column('wins', sa.Integer(), nullable=True),
    sa.Column('losses', sa.Integer(), nullable=True),
    sa.Column('ties', sa.Integer(), nullable=True),
    sa.Column('fpts', sa.DECIMAL(precision=6, scale=2), nullable=True),
    sa.Column('fpts_against', sa.DECIMAL(precision=6, scale=2), nullable=True),
    sa.Column('last_synced', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('roster_id', 'league_id'),
    sa.ForeignKeyConstraint(['league_id'], ['leagues.league_id'], )
    )
    op.create_index(op.f('ix_sleeper_rosters_league_id'), 'sleeper_rosters', ['league_id'], unique=False)

    # Migrate data back from rosters to sleeper_rosters
    op.execute("""
        INSERT INTO sleeper_rosters
        (roster_id, league_id, owner_id, player_ids, starters, reserve, taxi, settings,
         wins, losses, ties, fpts, fpts_against, created_at, updated_at)
        SELECT
            platform_roster_id, league_id, owner_id, player_ids, starters, reserve, taxi, settings,
            wins, losses, ties, fpts, fpts_against, created_at, updated_at
        FROM rosters
    """)

    # Drop the rosters table
    op.drop_index('ix_rosters_owner_league', table_name='rosters')
    op.drop_index('ix_rosters_league_platform', table_name='rosters')
    op.drop_index(op.f('ix_rosters_platform_roster_id'), table_name='rosters')
    op.drop_index(op.f('ix_rosters_league_id'), table_name='rosters')
    op.drop_table('rosters')
