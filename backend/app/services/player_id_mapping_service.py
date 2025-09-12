from typing import Dict, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.sleeper import SleeperPlayer
import logging
import difflib

logger = logging.getLogger(__name__)

# Team abbreviation mappings between providers
TEAM_MAPPINGS = {
    'fantasypros_to_sleeper': {
        'JAC': 'JAX',  # Jacksonville Jaguars (FP: JAC, Sleeper: JAX)
        # All other teams appear to match between FantasyPros and Sleeper:
        # DEN, PHI, MIN, PIT, BAL, HOU, BUF, DET, LAR, SEA, NE, KC, GB, 
        # NYJ, ARI, CHI, WAS, SF, LAC, NYG, TB, DAL, MIA, CLE, IND, ATL, 
        # CIN, NO, LV, TEN, CAR all match exactly
    }
}

# Defense name mappings from FantasyPros full names to Sleeper team abbreviations
DEFENSE_NAME_MAPPINGS = {
    'Arizona Cardinals': 'ARI',
    'Atlanta Falcons': 'ATL', 
    'Baltimore Ravens': 'BAL',
    'Buffalo Bills': 'BUF',
    'Carolina Panthers': 'CAR',
    'Chicago Bears': 'CHI',
    'Cincinnati Bengals': 'CIN',
    'Cleveland Browns': 'CLE',
    'Dallas Cowboys': 'DAL',
    'Denver Broncos': 'DEN',
    'Detroit Lions': 'DET',
    'Green Bay Packers': 'GB',
    'Houston Texans': 'HOU',
    'Indianapolis Colts': 'IND',
    'Jacksonville Jaguars': 'JAX',  # Note: JAX not JAC
    'Kansas City Chiefs': 'KC',
    'Las Vegas Raiders': 'LV',
    'Los Angeles Chargers': 'LAC',
    'Los Angeles Rams': 'LAR',
    'Miami Dolphins': 'MIA',
    'Minnesota Vikings': 'MIN',
    'New England Patriots': 'NE',
    'New Orleans Saints': 'NO',
    'New York Giants': 'NYG',
    'New York Jets': 'NYJ',
    'Philadelphia Eagles': 'PHI',
    'Pittsburgh Steelers': 'PIT',
    'San Francisco 49ers': 'SF',
    'Seattle Seahawks': 'SEA',
    'Tampa Bay Buccaneers': 'TB',
    'Tennessee Titans': 'TEN',
    'Washington Commanders': 'WAS',
}

def normalize_team_abbreviation(team: str, from_provider: str, to_provider: str) -> str:
    """Convert team abbreviation from one provider format to another"""
    if not team:
        return team
    
    mapping_key = f"{from_provider}_to_{to_provider}"
    mapping = TEAM_MAPPINGS.get(mapping_key, {})
    
    return mapping.get(team.upper(), team.upper())

class PlayerIDMappingService:
    """Service for managing player ID mappings across different sources"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_player_by_external_id(self, source_name: str, external_id: str) -> Optional[SleeperPlayer]:
        """Find a player by their external ID from a specific source"""
        
        # Map source names to database columns
        source_column_map = {
            'espn': SleeperPlayer.espn_id,
            'rotowire': SleeperPlayer.rotowire_id,
            'fantasy_data': SleeperPlayer.fantasy_data_id,
            'yahoo': SleeperPlayer.yahoo_id,
            'stats': SleeperPlayer.stats_id
        }
        
        column = source_column_map.get(source_name.lower())
        if not column:
            logger.warning(f"Unknown source: {source_name}")
            return None
        
        return self.db.query(SleeperPlayer).filter(column == external_id).first()
    
    def get_external_id(self, sleeper_player_id: str, source_name: str) -> Optional[str]:
        """Get a player's external ID for a specific source"""
        
        player = self.db.query(SleeperPlayer).filter(
            SleeperPlayer.sleeper_player_id == sleeper_player_id
        ).first()
        
        if not player:
            return None
        
        # Map source names to player attributes
        source_attr_map = {
            'espn': 'espn_id',
            'rotowire': 'rotowire_id', 
            'fantasy_data': 'fantasy_data_id',
            'yahoo': 'yahoo_id',
            'stats': 'stats_id'
        }
        
        attr_name = source_attr_map.get(source_name.lower())
        if not attr_name:
            logger.warning(f"Unknown source: {source_name}")
            return None
        
        return getattr(player, attr_name, None)
    
    def get_all_external_ids(self, sleeper_player_id: str) -> Dict[str, Optional[str]]:
        """Get all external IDs for a player"""
        
        player = self.db.query(SleeperPlayer).filter(
            SleeperPlayer.sleeper_player_id == sleeper_player_id
        ).first()
        
        if not player:
            return {}
        
        return {
            'espn': player.espn_id,
            'rotowire': player.rotowire_id,
            'fantasy_data': player.fantasy_data_id,
            'yahoo': player.yahoo_id,
            'stats': player.stats_id,
            'sleeper': player.sleeper_player_id
        }
    
    def find_players_with_external_id(self, source_name: str) -> List[SleeperPlayer]:
        """Find all players that have an external ID for a specific source"""
        
        source_column_map = {
            'espn': SleeperPlayer.espn_id,
            'rotowire': SleeperPlayer.rotowire_id,
            'fantasy_data': SleeperPlayer.fantasy_data_id,
            'yahoo': SleeperPlayer.yahoo_id,
            'stats': SleeperPlayer.stats_id
        }
        
        column = source_column_map.get(source_name.lower())
        if not column:
            logger.warning(f"Unknown source: {source_name}")
            return []
        
        return self.db.query(SleeperPlayer).filter(column.isnot(None)).all()
    
    def get_mapping_coverage_stats(self) -> Dict[str, int]:
        """Get statistics on external ID coverage"""
        
        total_players = self.db.query(SleeperPlayer).count()
        
        stats = {
            'total_players': total_players,
            'espn_coverage': self.db.query(SleeperPlayer).filter(SleeperPlayer.espn_id.isnot(None)).count(),
            'rotowire_coverage': self.db.query(SleeperPlayer).filter(SleeperPlayer.rotowire_id.isnot(None)).count(),
            'fantasy_data_coverage': self.db.query(SleeperPlayer).filter(SleeperPlayer.fantasy_data_id.isnot(None)).count(),
            'yahoo_coverage': self.db.query(SleeperPlayer).filter(SleeperPlayer.yahoo_id.isnot(None)).count(),
            'stats_coverage': self.db.query(SleeperPlayer).filter(SleeperPlayer.stats_id.isnot(None)).count()
        }
        
        # Calculate percentages
        for key in list(stats.keys()):
            if key != 'total_players' and total_players > 0:
                percentage_key = key.replace('_coverage', '_percentage')
                stats[percentage_key] = round((stats[key] / total_players) * 100, 2)
        
        return stats
    
    def update_external_id(self, sleeper_player_id: str, source_name: str, external_id: str) -> bool:
        """Update a player's external ID for a specific source"""
        
        player = self.db.query(SleeperPlayer).filter(
            SleeperPlayer.sleeper_player_id == sleeper_player_id
        ).first()
        
        if not player:
            logger.warning(f"Player {sleeper_player_id} not found")
            return False
        
        source_attr_map = {
            'espn': 'espn_id',
            'rotowire': 'rotowire_id',
            'fantasy_data': 'fantasy_data_id', 
            'yahoo': 'yahoo_id',
            'stats': 'stats_id'
        }
        
        attr_name = source_attr_map.get(source_name.lower())
        if not attr_name:
            logger.warning(f"Unknown source: {source_name}")
            return False
        
        setattr(player, attr_name, external_id)
        
        try:
            self.db.commit()
            logger.info(f"Updated {source_name} ID for player {sleeper_player_id}: {external_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update external ID: {e}")
            self.db.rollback()
            return False
    
    def find_fantasypros_player_match(self, fp_player: Dict) -> Optional[SleeperPlayer]:
        """
        Find matching Sleeper player for a FantasyPros player
        Uses multiple matching strategies in order of reliability
        """
        
        fp_name = fp_player.get('name', '').strip()
        fp_team_raw = fp_player.get('team_id', '').strip().upper()
        fp_position = fp_player.get('position_id', '').strip().upper()
        
        # Special handling for defenses (DST)
        if fp_position == 'DST':
            return self._find_defense_match(fp_name, fp_team_raw)
        
        # Normalize team abbreviation from FantasyPros to Sleeper format
        fp_team = normalize_team_abbreviation(fp_team_raw, 'fantasypros', 'sleeper')
        
        if not fp_name:
            return None
        
        # Strategy 1: Exact name and team match
        exact_match = self._find_exact_name_team_match(fp_name, fp_team, fp_position)
        if exact_match:
            logger.debug(f"Exact match found for {fp_name}: {exact_match.sleeper_player_id}")
            return exact_match
        
        # Strategy 2: Name variations (handle common differences)
        name_match = self._find_name_variation_match(fp_name, fp_team, fp_position)
        if name_match:
            logger.debug(f"Name variation match found for {fp_name}: {name_match.sleeper_player_id}")
            return name_match
        
        # Strategy 3: Fuzzy name matching (for similar names)
        fuzzy_match = self._find_fuzzy_name_match(fp_name, fp_team, fp_position)
        if fuzzy_match:
            logger.debug(f"Fuzzy match found for {fp_name}: {fuzzy_match.sleeper_player_id}")
            return fuzzy_match
        
        # Strategy 4: Fallback - try matching without team (name + position only)
        if fp_team:  # Only if we had a team to begin with
            fallback_match = self._find_exact_name_team_match(fp_name, None, fp_position)
            if fallback_match:
                logger.debug(f"Fallback match found for {fp_name} (ignoring team): {fallback_match.sleeper_player_id}")
                return fallback_match
        
        logger.warning(f"No match found for FantasyPros player: {fp_name} ({fp_team_raw}->{fp_team} {fp_position})")
        return None
    
    def _find_exact_name_team_match(self, name: str, team: Optional[str], position: str) -> Optional[SleeperPlayer]:
        """Find player by exact name and team match"""
        query = self.db.query(SleeperPlayer).filter(
            func.lower(SleeperPlayer.full_name) == func.lower(name)
        )
        
        if team:
            query = query.filter(func.upper(SleeperPlayer.team) == team.upper())
        
        if position:
            query = query.filter(func.upper(SleeperPlayer.position) == position.upper())
        
        return query.first()
    
    def _find_defense_match(self, fp_name: str, fp_team: str) -> Optional[SleeperPlayer]:
        """Find defense match using team name mappings"""
        
        # Map FantasyPros full team name to Sleeper team abbreviation
        sleeper_team = DEFENSE_NAME_MAPPINGS.get(fp_name)
        
        if not sleeper_team:
            logger.warning(f"No defense mapping found for: {fp_name}")
            return None
        
        # Find defense in Sleeper database
        defense = self.db.query(SleeperPlayer).filter(
            SleeperPlayer.sleeper_player_id == sleeper_team,
            SleeperPlayer.position == 'DEF'
        ).first()
        
        if defense:
            logger.debug(f"Defense match found: {fp_name} -> {sleeper_team}")
            return defense
        else:
            logger.warning(f"Defense not found in database: {sleeper_team}")
            return None
    
    def _find_name_variation_match(self, name: str, team: str, position: str) -> Optional[SleeperPlayer]:
        """Find player by handling common name variations"""
        
        # Handle common name variations
        variations = [
            name,
            name.replace('Jr.', 'Jr'),
            name.replace('Jr', 'Jr.'),
            name.replace('Sr.', 'Sr'),
            name.replace('Sr', 'Sr.'),
            name.replace(' III', ''),
            name.replace(' II', ''),
            name + ' Jr.',
            name + ' Sr.'
        ]
        
        # Also try without middle names/initials
        name_parts = name.split()
        if len(name_parts) >= 3:
            variations.append(f"{name_parts[0]} {name_parts[-1]}")
        
        for variation in variations:
            if variation == name:
                continue  # Skip the original, already tried
            
            match = self._find_exact_name_team_match(variation, team, position)
            if match:
                return match
        
        return None
    
    def _find_fuzzy_name_match(self, name: str, team: str, position: str, threshold: float = 0.8) -> Optional[SleeperPlayer]:
        """Find player using fuzzy string matching"""
        
        # Get candidates (same team and position if available)
        query = self.db.query(SleeperPlayer)
        
        if team:
            query = query.filter(func.upper(SleeperPlayer.team) == team)
        
        if position:
            query = query.filter(func.upper(SleeperPlayer.position) == position)
        
        candidates = query.all()
        
        best_match = None
        best_ratio = 0
        
        for candidate in candidates:
            if not candidate.full_name:
                continue
            
            ratio = difflib.SequenceMatcher(None, name.lower(), candidate.full_name.lower()).ratio()
            
            if ratio > best_ratio and ratio >= threshold:
                best_ratio = ratio
                best_match = candidate
        
        if best_match:
            logger.debug(f"Fuzzy match: '{name}' -> '{best_match.full_name}' (ratio: {best_ratio})")
        
        return best_match
    
    def create_fantasypros_mapping_batch(self, fp_players: List[Dict]) -> Dict[str, str]:
        """
        Create a batch mapping of FantasyPros players to Sleeper IDs
        Returns dict: {fantasypros_player_key: sleeper_player_id}
        """
        
        mapping = {}
        matched_count = 0
        
        for fp_player in fp_players:
            fp_key = self._create_fantasypros_key(fp_player)
            sleeper_player = self.find_fantasypros_player_match(fp_player)
            
            if sleeper_player:
                mapping[fp_key] = sleeper_player.sleeper_player_id
                matched_count += 1
        
        match_percentage = (matched_count / len(fp_players) * 100) if fp_players else 0
        logger.info(f"FantasyPros mapping: {matched_count}/{len(fp_players)} players matched ({match_percentage:.1f}%)")
        
        return mapping
    
    def _create_fantasypros_key(self, fp_player: Dict) -> str:
        """Create a unique key for a FantasyPros player"""
        name = fp_player.get('name', '')
        team = fp_player.get('team_id', '')
        position = fp_player.get('position_id', '')
        fpid = fp_player.get('fpid', '')
        
        return f"{name}|{team}|{position}|{fpid}"
    
    def get_fantasypros_mapping_stats(self, fp_players: List[Dict]) -> Dict:
        """Get statistics on FantasyPros mapping coverage"""
        
        if not fp_players:
            return {'total_players': 0, 'matched_players': 0, 'match_percentage': 0}
        
        mapping = self.create_fantasypros_mapping_batch(fp_players)
        matched_count = len(mapping)
        
        return {
            'total_players': len(fp_players),
            'matched_players': matched_count,
            'match_percentage': round((matched_count / len(fp_players)) * 100, 2)
        }