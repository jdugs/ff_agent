from sqlalchemy import Column, String, Integer, Enum, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class NFLTeam(Base):
    __tablename__ = "nfl_teams"
    
    team_code = Column(String(10), primary_key=True)
    team_name = Column(String(50), nullable=False)
    city = Column(String(50), nullable=False)
    conference = Column(Enum('AFC', 'NFC', name='conference'), nullable=False)
    division = Column(Enum('North', 'South', 'East', 'West', name='division'), nullable=False)
    
    # Relationships
    players = relationship("Player", back_populates="team")

class Player(Base, TimestampMixin):
    __tablename__ = "players"
    
    player_id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False, index=True)
    position = Column(String(10), nullable=False, index=True)
    nfl_team = Column(String(10), ForeignKey('nfl_teams.team_code'), nullable=False, index=True)
    bye_week = Column(Integer)
    injury_status = Column(String(50))
    years_pro = Column(Integer)
    
    # Relationships
    team = relationship("NFLTeam", back_populates="players")
    rankings = relationship("Ranking", back_populates="player")
    projections = relationship("PlayerProjection", back_populates="player")
    news_events = relationship("NewsEvent", back_populates="player")