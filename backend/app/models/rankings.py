from sqlalchemy import Column, String, Integer, Enum, DECIMAL, DateTime, JSON, Text, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class Ranking(Base):
    __tablename__ = "rankings"
    
    ranking_id = Column(BigInteger, primary_key=True, autoincrement=True)
    player_id = Column(String(50), ForeignKey('players.player_id'), nullable=False, index=True)
    source_id = Column(Integer, ForeignKey('sources.source_id'), nullable=False, index=True)
    week = Column(Integer, nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    season_type = Column(Enum('preseason', 'regular', 'playoffs', name='season_type'), default='regular')
    position_rank = Column(Integer)
    overall_rank = Column(Integer)
    projection = Column(DECIMAL(5, 2))
    confidence_level = Column(Enum('low', 'medium', 'high', name='confidence_level'), default='medium')
    league_type = Column(Enum('standard', 'ppr', 'half_ppr', 'superflex', name='league_type'), default='ppr')
    
    # Enhanced metadata for different source types
    tier = Column(Integer)
    expert_count = Column(Integer)
    rank_std = Column(DECIMAL(4, 2))
    rank_min = Column(Integer)
    rank_max = Column(Integer)
    expert_id = Column(Integer, index=True)
    expert_name = Column(String(100))
    
    timestamp = Column(DateTime, default=func.now(), nullable=False, index=True)
    raw_data = Column(JSON)
    
    # Relationships
    player = relationship("Player", back_populates="rankings")
    source = relationship("Source", back_populates="rankings")

class PlayerProjection(Base):
    __tablename__ = "player_projections"
    
    projection_id = Column(BigInteger, primary_key=True, autoincrement=True)
    player_id = Column(String(50), ForeignKey('players.player_id'), nullable=False, index=True)
    source_id = Column(Integer, ForeignKey('sources.source_id'), nullable=False, index=True)
    week = Column(Integer, nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    league_type = Column(Enum('standard', 'ppr', 'half_ppr', 'superflex', name='league_type'), default='ppr')
    
    # Passing stats
    pass_att = Column(DECIMAL(4, 1))
    pass_cmp = Column(DECIMAL(4, 1))
    pass_yds = Column(DECIMAL(5, 1))
    pass_tds = Column(DECIMAL(3, 1))
    pass_ints = Column(DECIMAL(3, 1))
    
    # Rushing stats
    rush_att = Column(DECIMAL(4, 1))
    rush_yds = Column(DECIMAL(5, 1))
    rush_tds = Column(DECIMAL(3, 1))
    
    # Receiving stats
    rec_rec = Column(DECIMAL(4, 1))
    rec_yds = Column(DECIMAL(5, 1))
    rec_tds = Column(DECIMAL(3, 1))
    rec_tgt = Column(DECIMAL(4, 1))
    
    # Kicking stats
    fg_made = Column(DECIMAL(3, 1))
    fg_att = Column(DECIMAL(3, 1))
    xp_made = Column(DECIMAL(3, 1))
    xp_att = Column(DECIMAL(3, 1))
    
    # Defense stats
    def_sack = Column(DECIMAL(3, 1))
    def_int = Column(DECIMAL(3, 1))
    def_fum_rec = Column(DECIMAL(3, 1))
    def_td = Column(DECIMAL(3, 1))
    def_safety = Column(DECIMAL(3, 1))
    def_pa = Column(Integer)  # Points allowed
    def_ya = Column(Integer)  # Yards allowed
    
    # Calculated fantasy points
    projected_points = Column(DECIMAL(5, 2))
    
    # Source-specific metadata
    source_metadata = Column(JSON)
    
    timestamp = Column(DateTime, default=func.now(), nullable=False)
    raw_response = Column(JSON)
    
    # Relationships
    player = relationship("Player", back_populates="projections")
    source = relationship("Source", back_populates="projections")