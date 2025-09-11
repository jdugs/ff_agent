from sqlalchemy import Column, String, Integer, Enum, DateTime, Text, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class NewsEvent(Base):
    __tablename__ = "news_events"
    
    event_id = Column(BigInteger, primary_key=True, autoincrement=True)
    player_id = Column(String(50), ForeignKey('players.player_id'), nullable=False, index=True)
    source_id = Column(Integer, ForeignKey('sources.source_id'), nullable=False, index=True)
    event_type = Column(Enum('injury', 'trade', 'depth_chart', 'suspension', 'weather', 'coach_comment', 'other', name='event_type'), nullable=False, index=True)
    severity = Column(Enum('low', 'medium', 'high', 'season_ending', name='severity'), default='medium', index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    impact_window = Column(String(50))
    timestamp = Column(DateTime, default=func.now(), nullable=False, index=True)
    url = Column(String(500))
    
    # Relationships
    player = relationship("Player", back_populates="news_events")
    source = relationship("Source", back_populates="news_events")