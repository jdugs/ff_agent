from sqlalchemy import Column, String, BigInteger, Integer, Enum, DECIMAL, DateTime, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base, TimestampMixin

class SleeperLeague(Base, TimestampMixin):
    __tablename__ = "sleeper_leagues"
    
    league_id = Column(String(50), primary_key=True)
    user_id = Column(String(50), nullable=False, index=True)
    sleeper_user_id = Column(String(50), nullable=False)
    league_name = Column(String(100))
    season = Column(String(10), nullable=False, index=True)
    status = Column(Enum('pre_draft', 'drafting', 'in_season', 'complete', name='league_status'), default='in_season')
    sport = Column(String(20), default='nfl')
    settings = Column(JSON)
    scoring_settings = Column(JSON)
    roster_positions = Column(JSON)
    total_rosters = Column(Integer)
    draft_id = Column(String(50))
    previous_league_id = Column(String(50))
    last_synced = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    rosters = relationship("SleeperRoster", back_populates="league")
    matchups = relationship("SleeperMatchup", back_populates="league")

class SleeperRoster(Base, TimestampMixin):
    __tablename__ = "sleeper_rosters"
    
    roster_id = Column(Integer, nullable=False, primary_key=True)
    league_id = Column(String(50), nullable=False, primary_key=True, index=True)
    owner_id = Column(String(50), index=True)
    player_ids = Column(JSON)
    starters = Column(JSON)
    reserve = Column(JSON)
    taxi = Column(JSON)
    settings = Column(JSON)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    ties = Column(Integer, default=0)
    fpts = Column(DECIMAL(6, 2), default=0)
    fpts_against = Column(DECIMAL(6, 2), default=0)
    last_synced = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    league = relationship("SleeperLeague", back_populates="rosters")

class SleeperPlayer(Base, TimestampMixin):
    __tablename__ = "sleeper_players"
    
    sleeper_player_id = Column(String(50), primary_key=True)
    player_id = Column(String(50), index=True)  # Link to our players table
    full_name = Column(String(100), index=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    position = Column(String(10), index=True)
    team = Column(String(10), index=True)
    age = Column(Integer)
    height = Column(String(10))
    weight = Column(String(10))
    college = Column(String(100))
    years_exp = Column(Integer)
    status = Column(Enum('Active', 'Inactive', 'Injured Reserve', 'Reserve/PUP', name='player_status'), default='Active')
    fantasy_positions = Column(JSON)
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    player = relationship("Player", back_populates="sleeper_mappings")

class SleeperMatchup(Base, TimestampMixin):
    __tablename__ = "sleeper_matchups"
    
    matchup_id = Column(BigInteger, primary_key=True, autoincrement=True)
    league_id = Column(String(50), nullable=False, index=True)
    week = Column(Integer, nullable=False, index=True)
    roster_id = Column(Integer, nullable=False, index=True)
    matchup_id_sleeper = Column(Integer)
    points = Column(DECIMAL(6, 2))
    points_for = Column(DECIMAL(6, 2))
    points_against = Column(DECIMAL(6, 2))
    starters = Column(JSON)
    starters_points = Column(JSON)
    players_points = Column(JSON)
    custom_points = Column(JSON)
    
    # Relationships
    league = relationship("SleeperLeague", back_populates="matchups")