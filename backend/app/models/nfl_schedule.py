from sqlalchemy import Column, String, Integer, DateTime, Boolean
from sqlalchemy.sql import func
from .base import Base, TimestampMixin

class NFLSchedule(Base, TimestampMixin):
    __tablename__ = "nfl_schedule"
    
    # Composite primary key: season + week + team
    season = Column(String(4), primary_key=True, nullable=False)  # e.g., "2025"
    week = Column(Integer, primary_key=True, nullable=False)
    team = Column(String(3), primary_key=True, nullable=False)  # Team abbreviation
    
    # Game details
    opponent = Column(String(3), nullable=False)
    is_home = Column(Boolean, nullable=False)
    game_time = Column(DateTime, nullable=True)
    game_time_str = Column(String(20), nullable=True)  # Formatted time string like "Sun 1:00 PM ET"
    
    # ESPN data
    espn_event_id = Column(String(20), nullable=True)
    game_date_raw = Column(String(50), nullable=True)  # Raw ESPN date string
    
    # Sync tracking
    last_synced = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<NFLSchedule(season={self.season}, week={self.week}, team={self.team}, opponent={self.opponent})>"