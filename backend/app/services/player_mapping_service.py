from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from app.models.players import Player
from app.models.sleeper import SleeperPlayer
from app.models.api_logs import PlayerIDMapping
from difflib import SequenceMatcher
import logging

logger = logging.getLogger(__name__)

class PlayerMappingService:
    """Service for mapping players between different systems"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def map_sleeper_to_player(self, sleeper_player_id: str) -> Optional[Player]:
        """Map a Sleeper player ID to our Player model"""
        # Check if mapping already exists
        mapping = self.db.query(PlayerIDMapping).filter(
            PlayerIDMapping.external_system == 'sleeper',
            PlayerIDMapping.external_player_id == sleeper_player_id
        ).first()
        
        if mapping:
            return self.db.query(Player).filter(Player.player_id == mapping.our_player_id).first()
        
        # Try to create mapping
        sleeper_player = self.db.query(SleeperPlayer).filter(
            SleeperPlayer.sleeper_player_id == sleeper_player_id
        ).first()
        
        if not sleeper_player:
            return None
        
        # Find matching player by name and position
        our_player = self._find_matching_player(sleeper_player)
        
        if our_player:
            # Create mapping
            self._create_mapping(our_player.player_id, 'sleeper', sleeper_player_id)
            return our_player
        
        return None
    
    def _find_matching_player(self, sleeper_player: SleeperPlayer) -> Optional[Player]:
        """Find matching player in our database"""
        if not sleeper_player.full_name or not sleeper_player.position:
            return None
        
        # Try exact match first
        exact_match = self.db.query(Player).filter(
            Player.name == sleeper_player.full_name,
            Player.position == sleeper_player.position
        ).first()
        
        if exact_match:
            return exact_match
        
        # Try fuzzy matching
        candidates = self.db.query(Player).filter(
            Player.position == sleeper_player.position
        ).all()
        
        best_match = None
        best_score = 0.8  # Minimum similarity threshold
        
        for candidate in candidates:
            similarity = SequenceMatcher(None, 
                                       sleeper_player.full_name.lower(), 
                                       candidate.name.lower()).ratio()
            
            if similarity > best_score:
                best_score = similarity
                best_match = candidate
        
        return best_match
    
    def _create_mapping(self, our_player_id: str, external_system: str, external_player_id: str, confidence: float = 1.0):
        """Create a new player ID mapping"""
        mapping = PlayerIDMapping(
            our_player_id=our_player_id,
            external_system=external_system,
            external_player_id=external_player_id,
            confidence_score=confidence,
            verified=confidence >= 0.95
        )
        self.db.add(mapping)
        self.db.commit()
    
    def get_sleeper_players_for_roster(self, player_ids: List[str]) -> List[Dict]:
        """Get player details for a list of Sleeper player IDs"""
        players = []
        for sleeper_id in player_ids:
            sleeper_player = self.db.query(SleeperPlayer).filter(
                SleeperPlayer.sleeper_player_id == sleeper_id
            ).first()
            
            if sleeper_player:
                our_player = self.map_sleeper_to_player(sleeper_id)
                players.append({
                    'sleeper_id': sleeper_id,
                    'sleeper_player': sleeper_player,
                    'our_player': our_player
                })
        
        return players