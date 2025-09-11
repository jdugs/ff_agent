from sqlalchemy import Column, String, Integer, Enum, Date, BigInteger
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class UserTeam(Base, TimestampMixin):
    __tablename__ = "user_teams"
    
    team_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=False, index=True)
    team_name = Column(String(100))
    league_type = Column(Enum('standard', 'ppr', 'half_ppr', 'superflex', name='league_type'), default='ppr')
    league_size = Column(Integer, default=12)
    
    # Relationships
    roster = relationship("TeamRoster", back_populates="team")

class TeamRoster(Base):
    __tablename__ = "team_rosters"
    
    roster_id = Column(BigInteger, primary_key=True, autoincrement=True)
    team_id = Column(Integer, nullable=False, index=True)
    player_id = Column(String(50), nullable=False, index=True)
    roster_position = Column(Enum('starter', 'bench', 'ir', name='roster_position'), default='bench')
    added_date = Column(Date)
    
    # Relationships
    team = relationship("UserTeam", back_populates="roster")
    player = relationship("Player")