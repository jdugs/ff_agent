import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://fantasy_user:fantasy_password@postgres:5432/fantasy_football"
    
    # API Keys
    fantasypros_api_key: str = ""
    
    # Sleeper API (no key required)
    sleeper_api_base: str = "https://api.sleeper.app/v1"
    sleeper_user_id: str = "1180399895784771584"  # Your Sleeper user ID
    sleeper_league_id: str = "1180279284862275584"  # Your current league ID
    
    # Season Configuration
    default_season: str = "2025"  # Current default season
    available_seasons: list = ["2023", "2024", "2025"]  # Seasons to support
    
    # Redis (for Celery)
    redis_url: str = "redis://redis:6379/0"
    
    # Environment
    environment: str = "development"
    debug: bool = True
    
    class Config:
        env_file = ".env"

settings = Settings()