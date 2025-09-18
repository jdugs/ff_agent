from sqlalchemy import Column, String, Integer, Enum, DECIMAL, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base, TimestampMixin

class NFLTeam(Base):
    __tablename__ = "nfl_teams"

    team_code = Column(String(10), primary_key=True)
    team_name = Column(String(50), nullable=False)
    city = Column(String(50), nullable=False)
    conference = Column(Enum('AFC', 'NFC', name='conference'), nullable=False)
    division = Column(Enum('North', 'South', 'East', 'West', name='division'), nullable=False)

    # Relationships
    players = relationship("Player", back_populates="nfl_team_rel")

class Player(Base, TimestampMixin):
    __tablename__ = "players"

    # Primary identifier - use Sleeper ID as primary key since it's most comprehensive
    player_id = Column(String(50), primary_key=True)  # This will be sleeper_player_id

    # Basic player info
    full_name = Column(String(100), nullable=False, index=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    position = Column(String(10), nullable=False, index=True)
    team = Column(String(10), ForeignKey('nfl_teams.team_code'), index=True)

    # Physical attributes
    age = Column(Integer)
    height = Column(String(10))
    weight = Column(String(10))
    college = Column(String(100))
    years_exp = Column(Integer)

    # Status and career info
    status = Column(Enum('Active', 'Inactive', 'Injured Reserve', 'Reserve/PUP',
                        'Practice Squad', 'Free Agent', name='player_status'),
                   default='Active', index=True)
    fantasy_positions = Column(JSON)  # Multiple eligible positions
    injury_status = Column(String(50))
    bye_week = Column(Integer)

    # External system IDs for multi-source integration
    sleeper_id = Column(String(50), index=True)  # Same as player_id for now
    espn_id = Column(String(50), index=True)
    yahoo_id = Column(String(50), index=True)
    fantasy_data_id = Column(String(50), index=True)
    rotowire_id = Column(String(50), index=True)
    stats_id = Column(String(50), index=True)
    nfl_gsis_id = Column(String(50), index=True)  # NFL's official ID
    pfr_id = Column(String(50), index=True)      # Pro Football Reference

    # Data source tracking
    primary_data_source = Column(String(20), default='sleeper')
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())
    data_quality_score = Column(DECIMAL(3, 2), default=1.00)  # Data completeness/accuracy

    # Relationships
    nfl_team_rel = relationship("NFLTeam", back_populates="players")
    rankings = relationship("Ranking", back_populates="player")
    projections = relationship("PlayerProjection", back_populates="player")
    news_events = relationship("NewsEvent", back_populates="player")
    player_stats = relationship("PlayerStats", back_populates="player")

    # Indexes for performance
    __table_args__ = (
        Index('ix_players_position_team', 'position', 'team'),
        Index('ix_players_status_position', 'status', 'position'),
        Index('ix_players_name_position', 'full_name', 'position'),
    )

    @property
    def name(self):
        """Backward compatibility property"""
        return self.full_name

    @property
    def nfl_team(self):
        """Backward compatibility property"""
        return self.team

    @property
    def years_pro(self):
        """Backward compatibility property"""
        return self.years_exp