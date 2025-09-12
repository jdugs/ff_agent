from typing import Dict, List, Optional, Any
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class FantasyProsAPIClient:
    """Client for FantasyPros Fantasy Football API"""
    
    def __init__(self):
        self.api_key = settings.fantasypros_api_key
        self.session = None
        if not self.api_key:
            logger.warning("FantasyPros API key not configured")
    
    async def _get_session(self):
        """Get or create HTTP session"""
        if not self.session:
            import httpx
            self.session = httpx.AsyncClient()
        return self.session
    
    async def get_projections(self, year: int = None, position: str = None, week: int = None) -> Dict[str, Any]:
        """
        Get player projections from FantasyPros
        
        Args:
            year: NFL season year (e.g., 2025)
            position: Player position (QB, RB, WR, TE, K, DST) - optional
            week: Specific week for weekly projections - optional (omit for season-long)
        
        Returns:
            Dictionary containing projection data
        """
        if not self.api_key:
            raise ValueError("FantasyPros API key not configured")
        
        # Default to current season if not specified
        if not year:
            year = int(settings.default_season)
        
        # Build URL
        url = f"public/v2/json/nfl/{year}/projections"
        
        # Build parameters
        params = {}
        if position:
            params['position'] = position.upper()
        if week:
            params['week'] = week
            
        return await self._make_request(url, params=params, headers={
            'x-api-key': self.api_key
        })
    
    def _get_base_url(self) -> str:
        """Get the base URL for FantasyPros API"""
        return "https://api.fantasypros.com/"
    
    async def _make_request(self, url, params=None, headers=None):
        """Make HTTP request"""
        session = await self._get_session()
        
        full_url = f"{self._get_base_url()}{url}"
        
        try:
            response = await session.get(full_url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"FantasyPros API request failed: {e}")
            raise