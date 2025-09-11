from sqlalchemy import Column, String, Integer, Enum, DateTime, JSON, Text, BigInteger, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base, TimestampMixin

class MatchupContext(Base, TimestampMixin):
    __tablename__ = "matchup_context"
    
    matchup_id = Column(BigInteger, primary_key=True, autoincrement=True)
    player_id = Column(String(50), nullable=False, index=True)
    week = Column(Integer, nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    opponent = Column(String(10), nullable=False)
    home_away = Column(Enum('home', 'away', name='home_away'), nullable=False)
    opponent_defense_rank_vs_pos = Column(Integer)
    weather_conditions = Column(String(100))
    temperature = Column(Integer)
    wind_speed = Column(Integer)
    precipitation = Column(String(50))
    vegas_implied_total = Column(DECIMAL(4, 1))
    vegas_spread = Column(DECIMAL(4, 1))
    pace_metrics = Column(JSON)
    injury_report_status = Column(Enum('out', 'doubtful', 'questionable', 'probable', 'healthy', name='injury_status'), default='healthy')
    snap_count_trend = Column(String(50))
    target_share_trend = Column(String(50))
    
    # Relationships
    player = relationship("Player")

class WaiverRecommendation(Base):
    __tablename__ = "waiver_recommendations"
    
    waiver_id = Column(BigInteger, primary_key=True, autoincrement=True)
    player_id = Column(String(50), nullable=False, index=True)
    source_id = Column(Integer, nullable=False, index=True)
    week = Column(Integer, nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    priority_level = Column(Enum('must_add', 'strong_add', 'decent_add', 'deep_league', name='priority_level'), nullable=False, index=True)
    reasoning = Column(Text)
    ownership_percentage = Column(DECIMAL(5, 2))
    add_percentage = Column(DECIMAL(5, 2))
    drop_candidates = Column(Text)
    timestamp = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    player = relationship("Player")
    source = relationship("Source")

class ActualFantasyResult(Base, TimestampMixin):
    __tablename__ = "actual_fantasy_results"
    
    result_id = Column(BigInteger, primary_key=True, autoincrement=True)
    player_id = Column(String(50), nullable=False, index=True)
    week = Column(Integer, nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    fantasy_points_standard = Column(DECIMAL(5, 2))
    fantasy_points_ppr = Column(DECIMAL(5, 2))
    fantasy_points_half_ppr = Column(DECIMAL(5, 2))
    snaps_played = Column(Integer)
    targets = Column(Integer)
    carries = Column(Integer)
    game_script = Column(String(50))
    
    # Relationships
    player = relationship("Player")