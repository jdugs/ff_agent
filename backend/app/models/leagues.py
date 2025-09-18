from sqlalchemy import Column, Boolean, String, Integer, Enum, JSON, Index, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class League(Base, TimestampMixin):
    __tablename__ = "leagues"

    league_id = Column(String(50), primary_key=True)
    platform = Column(String(20), nullable=False, index=True)  # 'sleeper', 'espn', 'yahoo', etc.
    platform_league_id = Column(String(50), nullable=False)  # Original platform ID
    league_name = Column(String(100))
    season = Column(String(10), nullable=False, index=True)

    # League configuration
    scoring_settings = Column(JSON)  # Platform-agnostic scoring rules
    roster_positions = Column(JSON)  # QB, RB, WR, etc.
    total_teams = Column(Integer)

    # League status and metadata
    status = Column(Enum('pre_draft', 'drafting', 'in_season', 'complete', name='league_status'), default='in_season')
    sport = Column(String(20), default='nfl')

    # Additional metadata
    user_id = Column(String(50), nullable=False, index=True)  # Owner/user who added this league
    is_active = Column(Boolean, default=True)

    # Relationships
    fantasy_point_calculations = relationship("FantasyPointCalculation", back_populates="league")
    rosters = relationship("Roster", back_populates="league")
    matchups = relationship("SleeperMatchup", back_populates="league")

    # Indexes for performance
    __table_args__ = (
        Index('ix_leagues_platform_season', 'platform', 'season'),
        Index('ix_leagues_user_season', 'user_id', 'season'),
        Index('ix_leagues_platform_id', 'platform', 'platform_league_id'),
    )

    def __repr__(self):
        return f"<League(id={self.league_id}, name={self.league_name}, platform={self.platform})>"