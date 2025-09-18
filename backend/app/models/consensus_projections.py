from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Boolean, Index
from sqlalchemy.sql import func
from .base import Base, TimestampMixin
import json


class ConsensusProjections(Base, TimestampMixin):
    """Cached consensus projections to improve dashboard performance"""
    __tablename__ = "consensus_projections"

    id = Column(Integer, primary_key=True, index=True)

    # Cache key components
    week = Column(Integer, nullable=True, index=True)  # NULL for season projections
    season = Column(String(4), nullable=False, index=True)
    position_filter = Column(String(10), nullable=True, index=True)  # NULL for all positions

    # Player information
    sleeper_player_id = Column(String(50), nullable=False, index=True)
    player_name = Column(String(100), nullable=False)
    team = Column(String(3), nullable=True)
    position = Column(String(10), nullable=False, index=True)

    # Consensus projection values
    fantasy_points = Column(Float, default=0)
    fantasy_points_standard = Column(Float, default=0)
    fantasy_points_half_ppr = Column(Float, default=0)

    # Offensive stats
    passing_yards = Column(Float, default=0)
    passing_tds = Column(Float, default=0)
    passing_interceptions = Column(Float, default=0)
    rushing_yards = Column(Float, default=0)
    rushing_tds = Column(Float, default=0)
    receiving_yards = Column(Float, default=0)
    receiving_tds = Column(Float, default=0)
    receptions = Column(Float, default=0)

    # Kicker stats
    field_goals_made = Column(Float, default=0)
    field_goals_attempted = Column(Float, default=0)
    extra_points_made = Column(Float, default=0)

    # Defense stats
    sacks = Column(Float, default=0)
    interceptions = Column(Float, default=0)
    fumble_recoveries = Column(Float, default=0)
    defensive_tds = Column(Float, default=0)

    # Consensus metadata
    provider_count = Column(Integer, default=1)
    total_weight = Column(Float, default=1.0)
    confidence_score = Column(Float, default=0.0)  # Based on provider agreement

    # Raw consensus data (JSON)
    raw_consensus_projections = Column(Text)  # JSON string of all consensus values
    individual_projections = Column(Text)  # JSON string of individual provider projections

    # Cache metadata
    cache_expires_at = Column(DateTime, nullable=False, index=True)
    is_stale = Column(Boolean, default=False, index=True)
    generation_duration_ms = Column(Integer)  # Time taken to generate consensus

    # Add indexes for common queries
    __table_args__ = (
        Index('idx_consensus_cache_key', 'week', 'season', 'position_filter'),
        Index('idx_consensus_player_lookup', 'sleeper_player_id', 'week', 'season'),
        Index('idx_consensus_position_week', 'position', 'week', 'season'),
        Index('idx_consensus_expires', 'cache_expires_at', 'is_stale'),
    )

    def get_consensus_projections_dict(self) -> dict:
        """Get consensus projections as a dictionary"""
        return {
            'fantasy_points': self.fantasy_points,
            'fantasy_points_standard': self.fantasy_points_standard,
            'fantasy_points_half_ppr': self.fantasy_points_half_ppr,
            'passing_yards': self.passing_yards,
            'passing_tds': self.passing_tds,
            'passing_interceptions': self.passing_interceptions,
            'rushing_yards': self.rushing_yards,
            'rushing_tds': self.rushing_tds,
            'receiving_yards': self.receiving_yards,
            'receiving_tds': self.receiving_tds,
            'receptions': self.receptions,
            'field_goals_made': self.field_goals_made,
            'field_goals_attempted': self.field_goals_attempted,
            'extra_points_made': self.extra_points_made,
            'sacks': self.sacks,
            'interceptions': self.interceptions,
            'fumble_recoveries': self.fumble_recoveries,
            'defensive_tds': self.defensive_tds,
        }

    def get_raw_consensus_projections(self) -> dict:
        """Get full raw consensus projections from JSON"""
        if self.raw_consensus_projections:
            try:
                return json.loads(self.raw_consensus_projections)
            except json.JSONDecodeError:
                return {}
        return {}

    def get_individual_projections(self) -> list:
        """Get individual provider projections from JSON"""
        if self.individual_projections:
            try:
                return json.loads(self.individual_projections)
            except json.JSONDecodeError:
                return []
        return []

    def set_raw_consensus_projections(self, projections: dict):
        """Store consensus projections as JSON"""
        self.raw_consensus_projections = json.dumps(projections)

    def set_individual_projections(self, projections: list):
        """Store individual provider projections as JSON"""
        self.individual_projections = json.dumps(projections)

    @staticmethod
    def generate_cache_key(week: int = None, season: str = None, position_filter: str = None) -> str:
        """Generate a cache key for lookups"""
        return f"consensus_{week or 'season'}_{season}_{position_filter or 'all'}"

    def __repr__(self):
        return f"<ConsensusProjections(player={self.player_name}, pos={self.position}, week={self.week}, fp={self.fantasy_points})>"