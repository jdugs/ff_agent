from sqlalchemy import Column, String, Integer, DECIMAL, DateTime, JSON, Text, BigInteger, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base, TimestampMixin

class APICallLog(Base):
    __tablename__ = "api_call_logs"
    
    log_id = Column(BigInteger, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey('sources.source_id'), nullable=False, index=True)
    endpoint = Column(String(200), nullable=False, index=True)
    http_method = Column(String(10), default='GET')
    status_code = Column(Integer)
    response_time_ms = Column(Integer)
    request_size_bytes = Column(Integer)
    response_size_bytes = Column(Integer)
    rate_limit_remaining = Column(Integer)
    rate_limit_reset_timestamp = Column(DateTime)
    error_message = Column(Text)
    request_params = Column(JSON)
    timestamp = Column(DateTime, default=func.now(), nullable=False, index=True)
    
    # Relationships
    source = relationship("Source")

class PlayerIDMapping(Base, TimestampMixin):
    __tablename__ = "player_id_mappings"
    
    mapping_id = Column(BigInteger, primary_key=True, autoincrement=True)
    our_player_id = Column(String(50), ForeignKey('players.player_id'), nullable=False, index=True)
    external_system = Column(String(50), nullable=False, index=True)
    external_player_id = Column(String(100), nullable=False, index=True)
    confidence_score = Column(DECIMAL(3, 2), default=1.00)
    verified = Column(Boolean, default=False)
    last_verified = Column(DateTime)
    
    # Relationships
    player = relationship("Player")