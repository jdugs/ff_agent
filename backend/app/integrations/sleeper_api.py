from typing import Dict, List, Optional, Any
from app.config import settings
from  app.integrations.base_api import BaseAPIClient
import logging

logger = logging.getLogger(__name__)

class SleeperAPIClient(BaseAPIClient):
    """Client for Sleeper Fantasy Football API"""
    
    def __init__(self):
        super().__init__("Sleeper League Data")
    
    async def get_user_by_username(self, username: str) -> Dict[str, Any]:
        """Get user information by username"""
        return await self._make_request(f"user/{username}")
    
    async def get_user_leagues(self, user_id: str, season: str = settings.default_season) -> List[Dict[str, Any]]:
        """Get all leagues for a user in a specific season"""
        return await self._make_request(f"user/{user_id}/leagues/nfl/{season}")
    
    async def get_league_info(self, league_id: str) -> Dict[str, Any]:
        """Get league information"""
        return await self._make_request(f"league/{league_id}")
    
    async def get_league_rosters(self, league_id: str) -> List[Dict[str, Any]]:
        """Get all rosters in a league"""
        return await self._make_request(f"league/{league_id}/rosters")
    
    async def get_league_users(self, league_id: str) -> List[Dict[str, Any]]:
        """Get all users in a league"""
        return await self._make_request(f"league/{league_id}/users")
    
    async def get_league_matchups(self, league_id: str, week: int) -> List[Dict[str, Any]]:
        """Get matchups for a specific week"""
        return await self._make_request(f"league/{league_id}/matchups/{week}")
    
    async def get_all_players(self) -> Dict[str, Any]:
        """Get all NFL players from Sleeper"""
        return await self._make_request("players/nfl")
    
    async def get_nfl_state(self) -> Dict[str, Any]:
        """Get current NFL season state"""
        return await self._make_request("state/nfl")
    
    async def get_player_stats(self, week: int, season: str = settings.default_season) -> Dict[str, Any]:
        """Get player stats for a specific week"""
        return await self._make_request(f"stats/nfl/regular/{season}/{week}")

    async def get_player_projections(self, week: int, season: str = settings.default_season) -> Dict[str, Any]:
        """Get player projections for a specific week"""
        return await self._make_request(f"projections/nfl/regular/{season}/{week}")

    async def get_matchup_details(self, league_id: str, week: int) -> List[Dict[str, Any]]:
        """Get detailed matchup data including individual player scores"""
        return await self._make_request(f"league/{league_id}/matchups/{week}")

    async def get_player_stats_individual(self, player_id: str, season: str = settings.default_season, season_type: str = "regular") -> Dict[str, Any]:
        """Get stats for an individual player"""
        return await self._make_request(f"stats/nfl/player/{player_id}?season_type={season_type}&season={season}")