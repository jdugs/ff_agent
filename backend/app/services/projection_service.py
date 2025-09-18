from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from app.integrations.fantasypros_api import FantasyProsAPIClient
from app.services.sleeper_service import SleeperService
from app.services.projection_sources import ProviderManager, DataCapability
from app.services.player_id_mapping_service import PlayerIDMappingService
from app.models.sleeper import SleeperPlayerProjections
from app.models.players import Player
from app.config import settings
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ProjectionService:
    """Service for collecting and aggregating player projections from multiple providers"""
    
    def __init__(self, db: Session):
        self.db = db
        self.provider_manager = ProviderManager()
        self.player_mapper = PlayerIDMappingService(db)
        
        # Initialize provider clients
        self.clients = {}
        self._init_clients()
    
    def _init_clients(self):
        """Initialize API clients for available providers"""
        try:
            if self.provider_manager.is_provider_available('fantasypros'):
                self.clients['fantasypros'] = FantasyProsAPIClient()
                logger.info("Initialized FantasyPros API client")
        except Exception as e:
            logger.error(f"Failed to initialize FantasyPros client: {e}")
        
        try:
            if self.provider_manager.is_provider_available('sleeper'):
                self.clients['sleeper'] = SleeperService(self.db)
                logger.info("Initialized Sleeper API client")
        except Exception as e:
            logger.error(f"Failed to initialize Sleeper client: {e}")
    
    async def collect_weekly_projections(self, week: int, season: str = None) -> Dict[str, Any]:
        """
        Collect weekly projections from all enabled sources
        
        Args:
            week: NFL week number
            season: NFL season (defaults to current season)
            
        Returns:
            Dictionary with source names as keys and projection data as values
        """
        if not season:
            season = settings.default_season
        
        projection_providers = self.provider_manager.get_projection_providers()
        logger.info(f"Collecting week {week} projections from providers: {projection_providers}")
        
        all_projections = {}
        
        for provider_name in projection_providers:
            try:
                projections = await self._collect_from_provider(provider_name, week=week, season=season)
                if projections:
                    all_projections[provider_name] = projections
                    logger.info(f"Collected {len(projections.get('players', []))} projections from {provider_name}")
            except Exception as e:
                logger.error(f"Failed to collect projections from {provider_name}: {e}")
                continue
        
        return all_projections
    
    async def collect_season_projections(self, season: str = None) -> Dict[str, Any]:
        """
        Collect season-long projections from all enabled sources
        
        Args:
            season: NFL season (defaults to current season)
            
        Returns:
            Dictionary with source names as keys and projection data as values
        """
        if not season:
            season = settings.default_season
        
        projection_providers = self.provider_manager.get_projection_providers()
        logger.info(f"Collecting season {season} projections from providers: {projection_providers}")
        
        all_projections = {}
        
        for provider_name in projection_providers:
            # Skip providers that don't support seasonal projections
            capabilities = self.provider_manager.get_provider_capabilities(provider_name)
            if not capabilities or not capabilities.supports_seasonal:
                logger.info(f"Skipping {provider_name} - doesn't support seasonal projections")
                continue
            
            try:
                projections = await self._collect_from_provider(provider_name, season=season)
                if projections:
                    all_projections[provider_name] = projections
                    logger.info(f"Collected {len(projections.get('players', []))} seasonal projections from {provider_name}")
            except Exception as e:
                logger.error(f"Failed to collect seasonal projections from {provider_name}: {e}")
                continue
        
        return all_projections
    
    async def _collect_from_provider(self, provider_name: str, week: int = None, season: str = None) -> Optional[Dict[str, Any]]:
        """Collect projections from a specific provider using capability routing"""
        
        client = self.clients.get(provider_name)
        if not client:
            logger.warning(f"No client available for provider: {provider_name}")
            return None
        
        # Route to the appropriate method based on provider
        if provider_name == 'fantasypros':
            return await self._collect_fantasypros_projections(client, week=week, season=season)
        elif provider_name == 'sleeper':
            return await self._collect_sleeper_projections(client, week=week, season=season)
        else:
            logger.warning(f"Unknown provider collection method for: {provider_name}")
            return None
    
    async def _collect_fantasypros_projections(self, client: FantasyProsAPIClient, week: int = None, season: str = None) -> Dict[str, Any]:
        """Collect projections from FantasyPros"""
        
        year = int(season) if season else int(settings.default_season)
        
        try:
            if week:
                # Weekly projections
                projections = await client.get_projections(year=year, week=week)
            else:
                # Season-long projections
                projections = await client.get_projections(year=year)
            
            return self._normalize_fantasypros_projections(projections)
        
        except Exception as e:
            logger.error(f"Failed to collect FantasyPros projections: {e}")
            return None
    
    async def _collect_sleeper_projections(self, client, week: int = None, season: str = None) -> Dict[str, Any]:
        """Collect projections from Sleeper"""
        
        if not week:
            logger.warning("Sleeper only supports weekly projections, week parameter required")
            return None
        
        try:
            # Sleeper projections are handled through their sync method
            # For now, we'll return existing projections from the database
            season_str = season or settings.default_season
            
            projections = self.db.query(SleeperPlayerProjections).filter(
                SleeperPlayerProjections.week == week,
                SleeperPlayerProjections.season == season_str
            ).all()
            
            return self._normalize_sleeper_projections(projections)
        
        except Exception as e:
            logger.error(f"Failed to collect Sleeper projections: {e}")
            return None
    
    def _normalize_fantasypros_projections(self, raw_projections: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize FantasyPros projection format"""
        
        players = raw_projections.get('players', [])
        normalized_players = []
        
        for player in players:
            stats = player.get('stats', {})
            normalized_player = {
                'source': 'fantasypros',
                'player_name': player.get('name', ''),
                'team': player.get('team_id', ''),
                'position': player.get('position_id', ''),
                'projections': {
                    'fantasy_points': stats.get('points_ppr', stats.get('points', 0)),
                    'passing_yards': stats.get('pass_yds', 0),
                    'passing_tds': stats.get('pass_tds', 0),
                    'passing_ints': stats.get('pass_ints', 0),
                    'rushing_yards': stats.get('rush_yds', 0),
                    'rushing_tds': stats.get('rush_tds', 0),
                    'receiving_yards': stats.get('rec_yds', 0),
                    'receiving_tds': stats.get('rec_tds', 0),
                    'receptions': stats.get('rec_rec', 0),
                },
                'raw_data': player
            }
            normalized_players.append(normalized_player)
        
        return {
            'players': normalized_players,
            'source': 'fantasypros',
            'timestamp': datetime.now().isoformat()
        }
    
    def _normalize_sleeper_projections(self, projections: List[SleeperPlayerProjections]) -> Dict[str, Any]:
        """Normalize Sleeper projection format"""
        
        normalized_players = []
        
        for projection in projections:
            player = projection.player  # Get the related Player
            
            normalized_player = {
                'source': 'sleeper',
                'player_name': player.full_name if player else 'Unknown',
                'team': player.team if player else '',
                'position': player.position if player else '',
                'sleeper_id': projection.sleeper_player_id,
                'projections': self._extract_all_projections(projection.raw_projections, player.position if player else ''),
                'raw_data': projection.raw_projections
            }
            normalized_players.append(normalized_player)
        
        return {
            'players': normalized_players,
            'source': 'sleeper',
            'timestamp': datetime.now().isoformat()
        }

    def _extract_all_projections(self, raw_projections: Dict, position: str) -> Dict[str, float]:
        """Extract all available projections with position-specific filtering"""
        if not raw_projections:
            return {}

        # Base projections available for all positions
        projections = {
            'fantasy_points': float(raw_projections.get('pts_ppr', 0)),
            'fantasy_points_standard': float(raw_projections.get('pts_std', 0)),
            'fantasy_points_half_ppr': float(raw_projections.get('pts_half_ppr', 0)),
        }

        # Offensive stats
        if position in ['QB', 'RB', 'WR', 'TE', 'FLEX']:
            projections.update({
                # Passing
                'passing_yards': raw_projections.get('pass_yd', 0),
                'passing_tds': raw_projections.get('pass_td', 0),
                'passing_attempts': raw_projections.get('pass_att', 0),
                'passing_completions': raw_projections.get('pass_cmp', 0),
                'passing_interceptions': raw_projections.get('pass_int', 0),

                # Rushing
                'rushing_yards': raw_projections.get('rush_yd', 0),
                'rushing_tds': raw_projections.get('rush_td', 0),
                'rushing_attempts': raw_projections.get('rush_att', 0),

                # Receiving
                'receiving_yards': raw_projections.get('rec_yd', 0),
                'receiving_tds': raw_projections.get('rec_td', 0),
                'receptions': raw_projections.get('rec', 0),
                'targets': raw_projections.get('rec_tgt', 0),

                # Negative plays
                'fumbles_lost': raw_projections.get('fum_lost', 0),
            })

        # Kicker stats
        if position == 'K':
            projections.update({
                'field_goals_made': raw_projections.get('fgm', 0),
                'field_goals_attempted': raw_projections.get('fga', 0),
                'extra_points_made': raw_projections.get('xpm', 0),
                'extra_points_attempted': raw_projections.get('xpa', 0),
                'field_goal_yards': raw_projections.get('fgm_yds', 0),

                # Distance-based FG makes
                'fg_0_19': raw_projections.get('fgm_0_19', 0),
                'fg_20_29': raw_projections.get('fgm_20_29', 0),
                'fg_30_39': raw_projections.get('fgm_30_39', 0),
                'fg_40_49': raw_projections.get('fgm_40_49', 0),
                'fg_50_plus': raw_projections.get('fgm_50p', 0),
            })

        # Defense stats
        if position == 'DEF':
            projections.update({
                'sacks': raw_projections.get('sack', 0),
                'interceptions': raw_projections.get('int', 0),
                'fumble_recoveries': raw_projections.get('fum_rec', 0),
                'defensive_tds': raw_projections.get('def_td', 0),
                'safeties': raw_projections.get('safe', 0),
                'blocked_kicks': raw_projections.get('blk_kick', 0),
                'fourth_down_stops': raw_projections.get('def_4_and_stop', 0),

                # Points allowed tiers
                'pts_allow_0': raw_projections.get('pts_allow_0', 0),
                'pts_allow_1_6': raw_projections.get('pts_allow_1_6', 0),
                'pts_allow_7_13': raw_projections.get('pts_allow_7_13', 0),
                'pts_allow_14_20': raw_projections.get('pts_allow_14_20', 0),
                'pts_allow_21_27': raw_projections.get('pts_allow_21_27', 0),
                'pts_allow_28_34': raw_projections.get('pts_allow_28_34', 0),
                'pts_allow_35_plus': raw_projections.get('pts_allow_35p', 0),

                # Yards allowed tiers
                'yds_allow_0_100': raw_projections.get('yds_allow_0_100', 0),
                'yds_allow_100_199': raw_projections.get('yds_allow_100_199', 0),
                'yds_allow_200_299': raw_projections.get('yds_allow_200_299', 0),
                'yds_allow_300_349': raw_projections.get('yds_allow_300_349', 0),
                'yds_allow_350_399': raw_projections.get('yds_allow_350_399', 0),
                'yds_allow_400_plus': raw_projections.get('yds_allow_400_449', 0),
            })

        return projections

    @staticmethod
    def get_position_display_stats(position: str) -> Dict[str, str]:
        """Get position-specific stats to display in UI with labels"""

        stat_mappings = {
            'QB': {
                'fantasy_points': 'Fantasy Points',
                'passing_yards': 'Pass Yds',
                'passing_tds': 'Pass TDs',
                'passing_interceptions': 'INTs',
                'rushing_yards': 'Rush Yds',
                'rushing_tds': 'Rush TDs',
                'fumbles_lost': 'Fumbles'
            },
            'RB': {
                'fantasy_points': 'Fantasy Points',
                'rushing_yards': 'Rush Yds',
                'rushing_tds': 'Rush TDs',
                'rushing_attempts': 'Carries',
                'receiving_yards': 'Rec Yds',
                'receiving_tds': 'Rec TDs',
                'receptions': 'Receptions',
                'fumbles_lost': 'Fumbles'
            },
            'WR': {
                'fantasy_points': 'Fantasy Points',
                'receiving_yards': 'Rec Yds',
                'receiving_tds': 'Rec TDs',
                'receptions': 'Receptions',
                'targets': 'Targets',
                'rushing_yards': 'Rush Yds',
                'rushing_tds': 'Rush TDs'
            },
            'TE': {
                'fantasy_points': 'Fantasy Points',
                'receiving_yards': 'Rec Yds',
                'receiving_tds': 'Rec TDs',
                'receptions': 'Receptions',
                'targets': 'Targets'
            },
            'K': {
                'fantasy_points': 'Fantasy Points',
                'field_goals_made': 'FG Made',
                'field_goals_attempted': 'FG Att',
                'extra_points_made': 'XP Made',
                'fg_40_49': 'FG 40-49',
                'fg_50_plus': 'FG 50+'
            },
            'DEF': {
                'fantasy_points': 'Fantasy Points',
                'sacks': 'Sacks',
                'interceptions': 'INTs',
                'fumble_recoveries': 'Fum Rec',
                'defensive_tds': 'Def TDs',
                'safeties': 'Safeties',
                'pts_allow_0': 'Shutouts',
                'blocked_kicks': 'Blocks'
            }
        }

        return stat_mappings.get(position, {
            'fantasy_points': 'Fantasy Points'
        })
    
    async def save_fantasypros_projections(self, week: Optional[int] = None, season: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch and save FantasyPros projections to database
        
        Args:
            week: NFL week (for weekly projections)
            season: NFL season (defaults to current season)
            
        Returns:
            Dictionary with save results
        """
        if not season:
            season = settings.default_season
        
        logger.info(f"Saving FantasyPros projections for {'week ' + str(week) if week else 'season'} {season}")
        
        # Get FantasyPros client
        fp_client = self.clients.get('fantasypros')
        if not fp_client:
            raise ValueError("FantasyPros client not available")
        
        # Collect projections from FantasyPros for all positions
        all_positions = ['QB', 'RB', 'WR', 'TE', 'K', 'DST']
        all_players = []
        
        for position in all_positions:
            try:
                if week:
                    position_data = await fp_client.get_projections(year=int(season), week=week, position=position)
                else:
                    position_data = await fp_client.get_projections(year=int(season), position=position)
                
                position_players = position_data.get('players', [])
                logger.info(f"Retrieved {len(position_players)} {position} projections from FantasyPros")
                all_players.extend(position_players)
            except Exception as e:
                logger.error(f"Error retrieving {position} projections: {e}")
        
        # Create the normalized data structure
        fp_data = {
            'players': [],
            'source': 'fantasypros',
            'timestamp': datetime.now().isoformat()
        }
        
        # Normalize all players
        for player in all_players:
            stats = player.get('stats', {})
            normalized_player = {
                'source': 'fantasypros',
                'player_name': player.get('name', ''),
                'team': player.get('team_id', ''),
                'position': player.get('position_id', ''),
                'projections': {
                    'fantasy_points': stats.get('points_ppr', stats.get('points', 0)),
                    'passing_yards': stats.get('pass_yds', 0),
                    'passing_tds': stats.get('pass_tds', 0),
                    'passing_ints': stats.get('pass_ints', 0),
                    'rushing_yards': stats.get('rush_yds', 0),
                    'rushing_tds': stats.get('rush_tds', 0),
                    'receiving_yards': stats.get('rec_yds', 0),
                    'receiving_tds': stats.get('rec_tds', 0),
                    'receptions': stats.get('rec_rec', 0),
                },
                'raw_data': player
            }
            fp_data['players'].append(normalized_player)
        
        logger.info(f"Total players collected across all positions: {len(fp_data['players'])}")
        
        if not fp_data or not fp_data.get('players'):
            logger.warning("No FantasyPros projection data to save")
            return {'saved': 0, 'errors': 0}
        
        # Save each player's projections
        saved_count = 0
        error_count = 0
        
        for player_data in fp_data['players']:
            try:
                success = await self._save_single_fantasypros_projection(player_data, week, season)
                if success:
                    saved_count += 1
                else:
                    error_count += 1
            except Exception as e:
                logger.error(f"Error saving projection for {player_data.get('player_name')}: {e}")
                error_count += 1
        
        logger.info(f"Saved {saved_count} FantasyPros projections, {error_count} errors")
        
        return {
            'saved': saved_count,
            'errors': error_count,
            'total_processed': len(fp_data['players']),
            'season': season,
            'week': week
        }
    
    async def _save_single_fantasypros_projection(self, player_data: Dict, week: Optional[int], season: str) -> bool:
        """Save a single FantasyPros player projection to database"""
        
        # Find matching Sleeper player using the raw data
        raw_player_data = player_data.get('raw_data', {})
        if not raw_player_data:
            logger.warning(f"No raw data for player: {player_data.get('player_name')}")
            return False
        
        sleeper_player = self.player_mapper.find_fantasypros_player_match(raw_player_data)
        if not sleeper_player:
            logger.debug(f"No Sleeper match for FantasyPros player: {player_data.get('player_name')}")
            return False
        
        # Get projection values
        projections = player_data.get('projections', {})
        
        try:
            # Check if projection already exists
            existing = self.db.query(SleeperPlayerProjections).filter(
                SleeperPlayerProjections.sleeper_player_id == sleeper_player.player_id,
                SleeperPlayerProjections.season == season,
                SleeperPlayerProjections.week == (week or 0)  # Use 0 for season-long
            ).first()
            
            if existing:
                # Update existing projection
                existing.projected_points_ppr = projections.get('fantasy_points', 0)
                existing.projected_points_standard = projections.get('fantasy_points', 0)  # Assume same for now
                existing.projected_points_half_ppr = projections.get('fantasy_points', 0)  # Assume same for now
                existing.proj_pass_yds = projections.get('passing_yards', 0)
                existing.proj_pass_tds = projections.get('passing_tds', 0)
                existing.proj_rush_yds = projections.get('rushing_yards', 0)
                existing.proj_rush_tds = projections.get('rushing_tds', 0)
                existing.proj_rec_yds = projections.get('receiving_yards', 0)
                existing.proj_rec_tds = projections.get('receiving_tds', 0)
                existing.proj_rec = projections.get('receptions', 0)
                existing.raw_projections = raw_player_data
                existing.updated_at = datetime.now()
                
                logger.debug(f"Updated existing projection for {sleeper_player.full_name}")
            else:
                # Create new projection
                new_projection = SleeperPlayerProjections(
                    sleeper_player_id=sleeper_player.player_id,
                    week=week or 0,  # Use 0 for season-long projections
                    season=season,
                    projected_points_ppr=projections.get('fantasy_points', 0),
                    projected_points_standard=projections.get('fantasy_points', 0),  # Assume same for now
                    projected_points_half_ppr=projections.get('fantasy_points', 0),  # Assume same for now
                    proj_pass_yds=projections.get('passing_yards', 0),
                    proj_pass_tds=projections.get('passing_tds', 0),
                    proj_rush_yds=projections.get('rushing_yards', 0),
                    proj_rush_tds=projections.get('rushing_tds', 0),
                    proj_rec_yds=projections.get('receiving_yards', 0),
                    proj_rec_tds=projections.get('receiving_tds', 0),
                    proj_rec=projections.get('receptions', 0),
                    raw_projections=raw_player_data
                )
                
                self.db.add(new_projection)
                logger.debug(f"Created new projection for {sleeper_player.full_name}")
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Database error saving projection for {sleeper_player.full_name}: {e}")
            self.db.rollback()
            return False
    
    async def get_saved_fantasypros_projections(self, week: Optional[int] = None, season: Optional[str] = None) -> Dict[str, Any]:
        """
        Get saved FantasyPros projections from database
        
        Args:
            week: NFL week (None for season-long projections, use 0 for season-long in DB)
            season: NFL season (defaults to current season)
            
        Returns:
            Dictionary with normalized projection data
        """
        if not season:
            season = settings.default_season
        
        # Convert week parameter (None = season-long stored as week 0)
        db_week = week if week is not None else 0
        
        logger.info(f"Loading saved FantasyPros projections for {'week ' + str(week) if week else 'season'} {season}")
        
        # Query saved projections
        projections_query = self.db.query(SleeperPlayerProjections).join(Player).filter(
            SleeperPlayerProjections.season == season,
            SleeperPlayerProjections.week == db_week
        )
        
        saved_projections = projections_query.all()
        
        if not saved_projections:
            logger.warning(f"No saved projections found for {'week ' + str(week) if week else 'season'} {season}")
            return {
                'players': [],
                'source': 'fantasypros_saved',
                'timestamp': datetime.now().isoformat()
            }
        
        # Convert to normalized format
        normalized_players = []
        for projection in saved_projections:
            player = projection.player  # Get related Player
            
            normalized_player = {
                'source': 'fantasypros_saved',
                'player_name': player.full_name if player else 'Unknown',
                'team': player.team if player else '',
                'position': player.position if player else '',
                'sleeper_id': projection.sleeper_player_id,
                'projections': {
                    'fantasy_points': float(projection.projected_points_ppr or 0),
                    'passing_yards': float(projection.proj_pass_yds or 0),
                    'passing_tds': float(projection.proj_pass_tds or 0),
                    'rushing_yards': float(projection.proj_rush_yds or 0),
                    'rushing_tds': float(projection.proj_rush_tds or 0),
                    'receiving_yards': float(projection.proj_rec_yds or 0),
                    'receiving_tds': float(projection.proj_rec_tds or 0),
                    'receptions': float(projection.proj_rec or 0),
                },
                'raw_data': projection.raw_projections or {}
            }
            normalized_players.append(normalized_player)
        
        logger.info(f"Loaded {len(normalized_players)} saved FantasyPros projections")
        
        return {
            'players': normalized_players,
            'source': 'fantasypros_saved',
            'timestamp': datetime.now().isoformat()
        }
    
    async def close(self):
        """Close all API clients"""
        for client in self.clients.values():
            if hasattr(client, 'close'):
                await client.close()