from sqlalchemy import Column, String, Integer, DECIMAL, JSON, BigInteger, ForeignKey, Index
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class Roster(Base, TimestampMixin):
    __tablename__ = "rosters"

    # Use a single auto-incrementing ID instead of composite primary key
    roster_id = Column(BigInteger, primary_key=True, autoincrement=True)

    # Platform-specific roster ID (e.g., Sleeper's roster_id)
    platform_roster_id = Column(Integer, nullable=False, index=True)

    # Link to generic leagues table
    league_id = Column(String(50), ForeignKey('leagues.league_id'), nullable=False, index=True)

    # Owner information
    owner_id = Column(String(50), index=True)  # Platform-specific user ID

    # Roster composition (JSON arrays of player IDs)
    player_ids = Column(JSON)
    starters = Column(JSON)
    reserve = Column(JSON)
    taxi = Column(JSON)

    # Roster settings and metadata
    settings = Column(JSON)

    # Season statistics
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    ties = Column(Integer, default=0)

    # Fantasy points
    fpts = Column(DECIMAL(6, 2), default=0)
    fpts_against = Column(DECIMAL(6, 2), default=0)

    # Relationships
    league = relationship("League", back_populates="rosters")

    # Indexes for performance
    __table_args__ = (
        Index('ix_rosters_league_platform', 'league_id', 'platform_roster_id'),
        Index('ix_rosters_owner_league', 'owner_id', 'league_id'),
    )

    def __repr__(self):
        return f"<Roster(id={self.roster_id}, league={self.league_id}, owner={self.owner_id})>"