from sqlalchemy import Column, String, Integer, Enum, DECIMAL, Boolean, DateTime, JSON, Text
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class Source(Base, TimestampMixin):
    __tablename__ = "sources"
    
    source_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    source_type = Column(Enum('rankings', 'news', 'analysis', 'consensus', 'social', 'league_data', name='source_type'), nullable=False, index=True)
    data_method = Column(Enum('web_scraping', 'api', 'manual', name='data_method'), default='web_scraping')
    base_weight = Column(DECIMAL(3, 2), default=1.00)
    current_reliability_score = Column(DECIMAL(3, 2))
    specialty = Column(String(50), index=True)
    update_frequency = Column(Enum('realtime', 'hourly', 'daily', 'weekly', name='update_frequency'), default='daily')
    
    # URL/API Configuration
    url_template = Column(String(500))
    api_base_url = Column(String(500))
    url_wildcards = Column(JSON)
    url_type = Column(Enum('static', 'templated', name='url_type'), default='static')
    last_successful_url = Column(String(500))
    
    # API-specific fields
    requires_api_key = Column(Boolean, default=False)
    api_key_name = Column(String(100))  # Environment variable name
    api_version = Column(String(20))
    rate_limit_per_hour = Column(Integer)
    rate_limit_per_day = Column(Integer)
    request_headers = Column(JSON)
    authentication_type = Column(Enum('none', 'api_key', 'bearer', 'basic', name='auth_type'), default='none')
    
    # General metadata
    is_premium = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    last_scraped = Column(DateTime)
    last_api_call = Column(DateTime)
    consecutive_failures = Column(Integer, default=0)
    
    # Relationships
    rankings = relationship("Ranking", back_populates="source")
    projections = relationship("PlayerProjection", back_populates="source")
    news_events = relationship("NewsEvent", back_populates="source")