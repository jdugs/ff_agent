from sqlalchemy import Column, String, DECIMAL, JSON, BigInteger, ForeignKey, Index
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class FantasyPointCalculation(Base, TimestampMixin):
    __tablename__ = "fantasy_point_calculations"

    calculation_id = Column(BigInteger, primary_key=True, autoincrement=True)
    league_id = Column(String(50), ForeignKey('leagues.league_id'), nullable=False, index=True)
    stat_id = Column(BigInteger, ForeignKey('player_stats.stat_id'), nullable=False, index=True)

    # Calculated fantasy points
    fantasy_points = Column(DECIMAL(6, 2), nullable=False)

    # Optional breakdown of how points were calculated
    scoring_breakdown = Column(JSON)  # e.g., {"passing_yards": 0.04, "passing_tds": 4.0, "total": 15.2}

    # Relationships
    league = relationship("League", back_populates="fantasy_point_calculations")
    player_stat = relationship("PlayerStats", back_populates="fantasy_point_calculations")

    # Indexes for performance
    __table_args__ = (
        Index('ix_fantasy_calculations_league_stat', 'league_id', 'stat_id'),
        Index('ix_fantasy_calculations_league_points', 'league_id', 'fantasy_points'),
    )

    def __repr__(self):
        return f"<FantasyPointCalculation(league={self.league_id}, stat={self.stat_id}, points={self.fantasy_points})>"