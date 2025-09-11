# Import all models in the correct order to avoid circular dependencies
from .base import Base
from .players import NFLTeam, Player  # NFLTeam first, then Player
from .sources import Source
from .rankings import Ranking, PlayerProjection
from .news import NewsEvent

# This ensures all models are registered with SQLAlchemy before relationships are resolved
__all__ = [
    "Base",
    "NFLTeam", "Player",  # NFLTeam first
    "Source", 
    "Ranking", "PlayerProjection",
    "NewsEvent"
]