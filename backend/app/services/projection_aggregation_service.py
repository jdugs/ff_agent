from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.services.projection_service import ProjectionService
from app.services.player_id_mapping_service import PlayerIDMappingService
from app.services.projection_sources import ProviderManager
from app.config import settings
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from statistics import mean, harmonic_mean
import time

logger = logging.getLogger(__name__)

@dataclass
class PlayerProjection:
    """Single player projection from one provider"""
    sleeper_id: str
    provider: str
    player_name: str
    team: str
    position: str
    projections: Dict[str, float]
    weight: float = 1.0
    raw_data: Dict = field(default_factory=dict)

@dataclass
class ConsensusProjection:
    """Aggregated consensus projection for a player"""
    sleeper_id: str
    player_name: str
    team: str
    position: str
    consensus_projections: Dict[str, float]
    provider_count: int
    total_weight: float
    individual_projections: List[PlayerProjection] = field(default_factory=list)

class ProjectionAggregationService:
    """Service for aggregating and creating consensus projections from multiple providers"""
    
    def __init__(self, db: Session):
        self.db = db
        self.projection_service = ProjectionService(db)
        self.mapping_service = PlayerIDMappingService(db)
        self.provider_manager = ProviderManager()
    
    async def create_consensus_projections(
        self,
        week: Optional[int] = None,
        season: Optional[str] = None,
        position_filter: Optional[str] = None,
        force_refresh: bool = False
    ) -> Dict[str, ConsensusProjection]:
        """
        Create consensus projections by aggregating data from multiple providers

        Args:
            week: NFL week (for weekly projections)
            season: NFL season (defaults to current season)
            position_filter: Optional position filter (QB, RB, WR, TE)
            force_refresh: Force regeneration even if cache exists

        Returns:
            Dict mapping sleeper_id to ConsensusProjection
        """

        if not season:
            season = settings.default_season

        # Check cache first (unless force_refresh is True)
        if not force_refresh:
            cached_projections = self._get_cached_consensus_projections(week, season, position_filter)
            if cached_projections:
                logger.info(f"Returning cached consensus projections for {'week ' + str(week) if week else 'season'} {season}")
                return cached_projections

        logger.info(f"Creating consensus projections for {'week ' + str(week) if week else 'season'} {season}")
        start_time = time.time()
        
        # Step 1: Collect projections from all providers (using saved data where available)
        raw_projections = {}
        
        # Get saved FantasyPros projections from database
        try:
            fp_saved_data = await self.projection_service.get_saved_fantasypros_projections(week=week, season=season)
            if fp_saved_data and fp_saved_data.get('players'):
                raw_projections['fantasypros'] = fp_saved_data
                logger.info(f"Loaded {len(fp_saved_data['players'])} FantasyPros projections from database")
        except Exception as e:
            logger.error(f"Failed to load saved FantasyPros projections: {e}")
        
        # Get Sleeper projections from database (if any exist)
        try:
            sleeper_data = await self.projection_service._collect_sleeper_projections(
                self.projection_service.clients.get('sleeper'), week=week, season=season
            )
            if sleeper_data and sleeper_data.get('players'):
                raw_projections['sleeper'] = sleeper_data
                logger.info(f"Loaded {len(sleeper_data['players'])} Sleeper projections")
        except Exception as e:
            logger.debug(f"No Sleeper projections available: {e}")
        
        # For now, focus on FantasyPros since that's what we have saved
        if not raw_projections:
            logger.warning("No projection data available for consensus calculation")
            return {}
        
        logger.info(f"Raw projections collected from {len(raw_projections)} providers")
        for provider, data in raw_projections.items():
            player_count = len(data.get('players', []))
            logger.info(f"Provider {provider}: {player_count} players")
        
        # Step 2: Normalize and map all projections to common player IDs
        normalized_projections = self._normalize_all_projections(raw_projections)
        
        # Step 3: Group projections by player
        grouped_projections = self._group_projections_by_player(normalized_projections)
        
        # Step 4: Create consensus projections
        consensus_projections = self._create_consensus_for_players(grouped_projections)
        
        # Step 5: Apply position filter if specified
        if position_filter:
            consensus_projections = {
                sleeper_id: proj for sleeper_id, proj in consensus_projections.items()
                if proj.position.upper() == position_filter.upper()
            }
        
        logger.info(f"Created consensus projections for {len(consensus_projections)} players")

        # Cache the results for future use
        generation_time_ms = int((time.time() - start_time) * 1000)
        self._cache_consensus_projections(consensus_projections, week, season, position_filter, generation_time_ms)

        # Cleanup
        await self.projection_service.close()

        return consensus_projections
    
    def _normalize_all_projections(self, raw_projections: Dict[str, Any]) -> List[PlayerProjection]:
        """Convert raw projections from all providers into normalized PlayerProjection objects"""
        
        normalized = []
        
        for provider_name, provider_data in raw_projections.items():
            provider_players = provider_data.get('players', [])
            provider_weight = self.provider_manager.get_provider_weight(provider_name)
            
            logger.info(f"Processing {len(provider_players)} players from {provider_name} (weight: {provider_weight})")
            
            for player_data in provider_players:
                normalized_projection = self._normalize_provider_projection(
                    provider_name, player_data, provider_weight
                )
                
                if normalized_projection:
                    normalized.append(normalized_projection)
                else:
                    logger.debug(f"Failed to normalize projection for {provider_name} player: {player_data.get('player_name', 'Unknown')}")
        
        logger.info(f"Normalized {len(normalized)} individual projections from {len(raw_projections)} providers")
        return normalized
    
    def _normalize_provider_projection(
        self, 
        provider_name: str, 
        player_data: Dict, 
        weight: float
    ) -> Optional[PlayerProjection]:
        """Normalize a single provider's player projection"""
        
        if provider_name == 'fantasypros':
            return self._normalize_fantasypros_projection(player_data, weight)
        elif provider_name == 'sleeper':
            return self._normalize_sleeper_projection(player_data, weight)
        else:
            logger.warning(f"Unknown provider for normalization: {provider_name}")
            return None
    
    def _normalize_fantasypros_projection(self, fp_data: Dict, weight: float) -> Optional[PlayerProjection]:
        """Normalize FantasyPros projection data"""
        
        # Check if this is saved data (already has sleeper_id) or live API data
        if fp_data.get('sleeper_id'):
            # This is saved data from database - already mapped
            sleeper_id = fp_data.get('sleeper_id')
            projections = fp_data.get('projections', {})
            
            return PlayerProjection(
                sleeper_id=sleeper_id,
                provider='fantasypros',
                player_name=fp_data.get('player_name', ''),
                team=fp_data.get('team', ''),
                position=fp_data.get('position', ''),
                projections=projections,
                weight=weight,
                raw_data=fp_data.get('raw_data', {})
            )
        else:
            # This is live API data - needs mapping
            source = fp_data.get('source', '')
            if not source.startswith('fantasypros'):
                logger.warning(f"Expected FantasyPros data but got: {source}")
                return None
            
            # Find matching Sleeper player using the original raw data
            raw_player_data = fp_data.get('raw_data', {})
            sleeper_player = self.mapping_service.find_fantasypros_player_match(raw_player_data)
            
            if not sleeper_player:
                logger.debug(f"No Sleeper match found for FantasyPros player: {fp_data.get('player_name')}")
                return None
            
            # Use the already normalized projections
            projections = fp_data.get('projections', {})
            
            return PlayerProjection(
                sleeper_id=sleeper_player.player_id,
                provider='fantasypros',
                player_name=sleeper_player.full_name or fp_data.get('player_name', ''),
                team=sleeper_player.team or fp_data.get('team', ''),
                position=sleeper_player.position or fp_data.get('position', ''),
                projections=projections,
                weight=weight,
                raw_data=raw_player_data
            )
    
    def _normalize_sleeper_projection(self, sleeper_data: Dict, weight: float) -> Optional[PlayerProjection]:
        """Normalize Sleeper projection data"""
        
        sleeper_id = sleeper_data.get('sleeper_id')
        if not sleeper_id:
            return None
        
        projections = sleeper_data.get('projections', {})
        
        return PlayerProjection(
            sleeper_id=sleeper_id,
            provider='sleeper',
            player_name=sleeper_data.get('player_name', ''),
            team=sleeper_data.get('team', ''),
            position=sleeper_data.get('position', ''),
            projections=projections,
            weight=weight,
            raw_data=sleeper_data
        )
    
    def _group_projections_by_player(self, projections: List[PlayerProjection]) -> Dict[str, List[PlayerProjection]]:
        """Group projections by player (sleeper_id)"""
        
        grouped = {}
        
        for projection in projections:
            sleeper_id = projection.sleeper_id
            
            if sleeper_id not in grouped:
                grouped[sleeper_id] = []
            
            grouped[sleeper_id].append(projection)
        
        logger.info(f"Grouped projections for {len(grouped)} unique players")
        return grouped
    
    def _create_consensus_for_players(self, grouped_projections: Dict[str, List[PlayerProjection]]) -> Dict[str, ConsensusProjection]:
        """Create consensus projections for each player"""
        
        consensus_projections = {}
        
        for sleeper_id, player_projections in grouped_projections.items():
            consensus = self._create_single_consensus(sleeper_id, player_projections)
            if consensus:
                consensus_projections[sleeper_id] = consensus
        
        return consensus_projections
    
    def _create_single_consensus(self, sleeper_id: str, projections: List[PlayerProjection]) -> Optional[ConsensusProjection]:
        """Create consensus projection for a single player from multiple provider projections"""
        
        if not projections:
            return None
        
        # Use first projection for basic player info
        base_projection = projections[0]
        
        # Get all unique projection fields
        all_fields = set()
        for proj in projections:
            all_fields.update(proj.projections.keys())
        
        # Calculate weighted consensus for each field
        consensus_values = {}
        total_weight = sum(proj.weight for proj in projections)
        
        for field in all_fields:
            values_and_weights = []
            
            for proj in projections:
                value = proj.projections.get(field, 0)
                if value is not None and value > 0:  # Only include non-zero values
                    # Convert to float to handle Decimal types from database
                    float_value = float(value) if value is not None else 0.0
                    values_and_weights.append((float_value, proj.weight))
            
            if values_and_weights:
                # Weighted average
                weighted_sum = sum(value * weight for value, weight in values_and_weights)
                weights_sum = sum(weight for _, weight in values_and_weights)
                consensus_values[field] = round(weighted_sum / weights_sum, 2) if weights_sum > 0 else 0
            else:
                consensus_values[field] = 0
        
        return ConsensusProjection(
            sleeper_id=sleeper_id,
            player_name=base_projection.player_name,
            team=base_projection.team,
            position=base_projection.position,
            consensus_projections=consensus_values,
            provider_count=len(projections),
            total_weight=total_weight,
            individual_projections=projections
        )
    
    def get_consensus_summary_stats(self, consensus_projections: Dict[str, ConsensusProjection]) -> Dict[str, Any]:
        """Get summary statistics for consensus projections"""
        
        if not consensus_projections:
            return {'total_players': 0, 'provider_coverage': {}, 'position_breakdown': {}}
        
        # Provider coverage stats
        provider_counts = {}
        position_counts = {}
        total_projections = 0
        
        for consensus in consensus_projections.values():
            # Count providers per player
            for proj in consensus.individual_projections:
                provider_counts[proj.provider] = provider_counts.get(proj.provider, 0) + 1
            
            # Count by position
            pos = consensus.position.upper()
            position_counts[pos] = position_counts.get(pos, 0) + 1
            
            total_projections += consensus.provider_count
        
        # Average projections per player
        avg_providers_per_player = total_projections / len(consensus_projections) if consensus_projections else 0
        
        return {
            'total_players': len(consensus_projections),
            'average_providers_per_player': round(avg_providers_per_player, 2),
            'provider_coverage': provider_counts,
            'position_breakdown': position_counts,
            'total_individual_projections': total_projections
        }

    def _get_cached_consensus_projections(
        self,
        week: Optional[int] = None,
        season: Optional[str] = None,
        position_filter: Optional[str] = None
    ) -> Optional[Dict[str, ConsensusProjection]]:
        """Get cached consensus projections if they exist and are fresh"""
        from app.models.consensus_projections import ConsensusProjections

        # Check for cached projections that haven't expired
        query = self.db.query(ConsensusProjections).filter(
            and_(
                ConsensusProjections.week == week,
                ConsensusProjections.season == season,
                ConsensusProjections.position_filter == position_filter,
                ConsensusProjections.cache_expires_at > datetime.now(),
                ConsensusProjections.is_stale == False
            )
        )

        cached_rows = query.all()
        if not cached_rows:
            return None

        # Convert cached rows back to ConsensusProjection objects
        consensus_projections = {}
        for row in cached_rows:
            individual_projections = []
            for individual_data in row.get_individual_projections():
                individual_projections.append(PlayerProjection(
                    sleeper_id=individual_data['sleeper_id'],
                    provider=individual_data['provider'],
                    player_name=individual_data['player_name'],
                    team=individual_data['team'],
                    position=individual_data['position'],
                    projections=individual_data['projections'],
                    weight=individual_data['weight']
                ))

            consensus_projections[row.sleeper_player_id] = ConsensusProjection(
                sleeper_id=row.sleeper_player_id,
                player_name=row.player_name,
                team=row.team,
                position=row.position,
                consensus_projections=row.get_raw_consensus_projections(),
                provider_count=row.provider_count,
                total_weight=row.total_weight,
                individual_projections=individual_projections
            )

        logger.info(f"Found {len(consensus_projections)} cached consensus projections")
        return consensus_projections

    def _cache_consensus_projections(
        self,
        consensus_projections: Dict[str, ConsensusProjection],
        week: Optional[int] = None,
        season: Optional[str] = None,
        position_filter: Optional[str] = None,
        generation_time_ms: int = 0
    ):
        """Cache consensus projections for future use"""
        from app.models.consensus_projections import ConsensusProjections

        # Clear existing cache for this query
        self.db.query(ConsensusProjections).filter(
            and_(
                ConsensusProjections.week == week,
                ConsensusProjections.season == season,
                ConsensusProjections.position_filter == position_filter
            )
        ).delete()

        # Cache expires in 30 minutes for current week, 4 hours for future weeks
        cache_duration_hours = 0.5 if week and week <= 3 else 4
        cache_expires_at = datetime.now() + timedelta(hours=cache_duration_hours)

        # Store each consensus projection
        for sleeper_id, consensus in consensus_projections.items():
            # Prepare individual projections for storage
            individual_data = []
            for proj in consensus.individual_projections:
                individual_data.append({
                    'sleeper_id': proj.sleeper_id,
                    'provider': proj.provider,
                    'player_name': proj.player_name,
                    'team': proj.team,
                    'position': proj.position,
                    'projections': proj.projections,
                    'weight': proj.weight
                })

            # Extract common projection fields
            proj_dict = consensus.consensus_projections

            cached_projection = ConsensusProjections(
                week=week,
                season=season,
                position_filter=position_filter,
                sleeper_player_id=sleeper_id,
                player_name=consensus.player_name,
                team=consensus.team,
                position=consensus.position,
                fantasy_points=proj_dict.get('fantasy_points', 0),
                fantasy_points_standard=proj_dict.get('fantasy_points_standard', 0),
                fantasy_points_half_ppr=proj_dict.get('fantasy_points_half_ppr', 0),
                passing_yards=proj_dict.get('passing_yards', 0),
                passing_tds=proj_dict.get('passing_tds', 0),
                passing_interceptions=proj_dict.get('passing_interceptions', 0),
                rushing_yards=proj_dict.get('rushing_yards', 0),
                rushing_tds=proj_dict.get('rushing_tds', 0),
                receiving_yards=proj_dict.get('receiving_yards', 0),
                receiving_tds=proj_dict.get('receiving_tds', 0),
                receptions=proj_dict.get('receptions', 0),
                field_goals_made=proj_dict.get('field_goals_made', 0),
                field_goals_attempted=proj_dict.get('field_goals_attempted', 0),
                extra_points_made=proj_dict.get('extra_points_made', 0),
                sacks=proj_dict.get('sacks', 0),
                interceptions=proj_dict.get('interceptions', 0),
                fumble_recoveries=proj_dict.get('fumble_recoveries', 0),
                defensive_tds=proj_dict.get('defensive_tds', 0),
                provider_count=consensus.provider_count,
                total_weight=consensus.total_weight,
                confidence_score=consensus.total_weight / consensus.provider_count if consensus.provider_count > 0 else 0,
                cache_expires_at=cache_expires_at,
                is_stale=False,
                generation_duration_ms=generation_time_ms
            )

            # Store JSON data
            cached_projection.set_raw_consensus_projections(consensus.consensus_projections)
            cached_projection.set_individual_projections(individual_data)

            self.db.add(cached_projection)

        try:
            self.db.commit()
            logger.info(f"Cached {len(consensus_projections)} consensus projections, expires at {cache_expires_at}")
        except Exception as e:
            logger.error(f"Failed to cache consensus projections: {e}")
            self.db.rollback()

    def invalidate_cache(
        self,
        week: Optional[int] = None,
        season: Optional[str] = None,
        position_filter: Optional[str] = None
    ):
        """Mark cached projections as stale"""
        from app.models.consensus_projections import ConsensusProjections

        query = self.db.query(ConsensusProjections)
        if week is not None:
            query = query.filter(ConsensusProjections.week == week)
        if season is not None:
            query = query.filter(ConsensusProjections.season == season)
        if position_filter is not None:
            query = query.filter(ConsensusProjections.position_filter == position_filter)

        query.update({ConsensusProjections.is_stale: True})
        self.db.commit()
        logger.info(f"Invalidated consensus projection cache for week={week}, season={season}, position={position_filter}")