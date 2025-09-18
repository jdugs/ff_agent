from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.services.projection_service import ProjectionService
from app.services.projection_sources import ProviderManager
from app.models.players import Player
from app.config import settings
from pydantic import BaseModel
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

class ProjectionTestResponse(BaseModel):
    """Response model for projection testing"""
    message: str
    sources_enabled: list
    projections_collected: dict
    total_players: int

@router.get("/test", response_model=ProjectionTestResponse)
async def test_projections(
    week: Optional[int] = Query(None, description="Week number for weekly projections"),
    season: str = Query(settings.default_season, description="NFL season"),
    db: Session = Depends(get_db)
):
    """Test projection collection from all enabled sources"""
    
    try:
        # Initialize services
        projection_service = ProjectionService(db)
        provider_manager = ProviderManager()
        
        # Get available providers
        enabled_providers = provider_manager.get_projection_providers()
        
        if not enabled_providers:
            raise HTTPException(status_code=400, detail="No projection providers are available")
        
        # Collect projections
        if week:
            projections = await projection_service.collect_weekly_projections(week, season)
        else:
            projections = await projection_service.collect_season_projections(season)
        
        # Count total players across all providers
        total_players = 0
        projections_summary = {}
        
        for provider_name, provider_projections in projections.items():
            player_count = len(provider_projections.get('players', []))
            projections_summary[provider_name] = {
                'player_count': player_count,
                'timestamp': provider_projections.get('timestamp')
            }
            total_players += player_count
        
        # Cleanup
        await projection_service.close()
        
        return ProjectionTestResponse(
            message=f"Successfully collected projections for {'week ' + str(week) if week else 'season'} {season}",
            sources_enabled=enabled_providers,
            projections_collected=projections_summary,
            total_players=total_players
        )
        
    except Exception as e:
        logger.error(f"Failed to test projections: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sources")
async def get_projection_sources(db: Session = Depends(get_db)):
    """Get information about projection sources"""
    
    try:
        provider_manager = ProviderManager()
        
        core_providers = provider_manager.get_providers()
        enabled_providers = provider_manager.get_projection_providers()
        
        provider_info = {}
        for provider_name, capabilities in core_providers.items():
            provider_info[provider_name] = {
                'capabilities': {
                    'has_projections': capabilities.has_projections,
                    'has_rankings': capabilities.has_rankings,
                    'has_stats': capabilities.has_stats,
                    'supports_weekly': capabilities.supports_weekly,
                    'supports_seasonal': capabilities.supports_seasonal
                },
                'enabled': provider_name in enabled_providers,
                'weight': capabilities.weight
            }
        
        return {
            'core_providers': provider_info,
            'enabled_projection_providers': enabled_providers
        }
        
    except Exception as e:
        logger.error(f"Failed to get source information: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fantasypros/test")
async def test_fantasypros_direct(
    week: Optional[int] = Query(None, description="Week number"),
    position: Optional[str] = Query(None, description="Position (QB, RB, WR, TE, K, DST)"),
    season: str = Query(settings.default_season, description="NFL season")
):
    """Test FantasyPros API directly"""
    
    try:
        from app.integrations.fantasypros_api import FantasyProsAPIClient
        
        client = FantasyProsAPIClient()
        
        if not client.api_key:
            raise HTTPException(status_code=400, detail="FantasyPros API key not configured")
        
        projections = await client.get_projections(
            year=int(season),
            week=week,
            position=position
        )
        
        return {
            'message': 'FantasyPros API test successful',
            'parameters': {
                'season': season,
                'week': week,
                'position': position
            },
            'player_count': len(projections.get('players', [])),
            'sample_players': projections.get('players', [])[:3]  # First 3 players as sample
        }
        
    except Exception as e:
        logger.error(f"FantasyPros API test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mapping/test")
async def test_player_mapping(
    position: Optional[str] = Query("QB", description="Position to test mapping for"),
    season: str = Query(settings.default_season, description="NFL season"),
    db: Session = Depends(get_db)
):
    """Test player ID mapping between FantasyPros and Sleeper"""
    
    try:
        from app.integrations.fantasypros_api import FantasyProsAPIClient
        from app.services.player_id_mapping_service import PlayerIDMappingService
        
        # Get FantasyPros data
        client = FantasyProsAPIClient()
        if not client.api_key:
            raise HTTPException(status_code=400, detail="FantasyPros API key not configured")
        
        fp_data = await client.get_projections(year=int(season), position=position)
        fp_players = fp_data.get('players', [])
        
        if not fp_players:
            raise HTTPException(status_code=404, detail=f"No FantasyPros players found for position {position}")
        
        # Test mapping
        mapping_service = PlayerIDMappingService(db)
        mapping_stats = mapping_service.get_fantasypros_mapping_stats(fp_players)
        
        # Get some example matches
        mapping = mapping_service.create_fantasypros_mapping_batch(fp_players[:10])  # First 10 for examples
        
        example_matches = []
        for fp_player in fp_players[:5]:  # Show first 5 matches as examples
            fp_key = mapping_service._create_fantasypros_key(fp_player)
            sleeper_id = mapping.get(fp_key)
            
            match_info = {
                'fantasypros_player': {
                    'name': fp_player.get('name'),
                    'team': fp_player.get('team_id'),
                    'position': fp_player.get('position_id'),
                    'fpid': fp_player.get('fpid')
                },
                'sleeper_id': sleeper_id,
                'matched': sleeper_id is not None
            }
            
            if sleeper_id:
                # Get Sleeper player details
                player = db.query(Player).filter(
                    Player.player_id == sleeper_id
                ).first()
                if player:
                    match_info['sleeper_player'] = {
                        'name': player.full_name,
                        'team': player.team,
                        'position': player.position
                    }
            
            example_matches.append(match_info)
        
        return {
            'message': f'Player mapping test completed for {position} position',
            'mapping_stats': mapping_stats,
            'example_matches': example_matches
        }
        
    except Exception as e:
        logger.error(f"Player mapping test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/consensus")
async def get_consensus_projections(
    week: Optional[int] = Query(None, description="Week number for weekly projections"),
    season: str = Query(settings.default_season, description="NFL season"),
    position: Optional[str] = Query(None, description="Position filter (QB, RB, WR, TE)"),
    limit: int = Query(50, description="Limit number of players returned"),
    db: Session = Depends(get_db)
):
    """Get consensus projections aggregated from multiple providers"""
    
    try:
        from app.services.projection_aggregation_service import ProjectionAggregationService
        
        # Initialize aggregation service
        aggregation_service = ProjectionAggregationService(db)
        
        # Create consensus projections
        consensus_projections = await aggregation_service.create_consensus_projections(
            week=week,
            season=season,
            position_filter=position
        )
        
        # Get summary stats
        summary_stats = aggregation_service.get_consensus_summary_stats(consensus_projections)
        
        # Convert to list and sort by fantasy points (descending)
        projections_list = []
        for sleeper_id, consensus in consensus_projections.items():
            proj_data = {
                'sleeper_id': sleeper_id,
                'player_name': consensus.player_name,
                'team': consensus.team,
                'position': consensus.position,
                'fantasy_points': consensus.consensus_projections.get('fantasy_points', 0),
                'consensus_projections': consensus.consensus_projections,
                'provider_count': consensus.provider_count,
                'total_weight': consensus.total_weight,
                'providers': [proj.provider for proj in consensus.individual_projections]
            }
            projections_list.append(proj_data)
        
        # Sort by fantasy points descending
        projections_list.sort(key=lambda x: x['fantasy_points'], reverse=True)
        
        # Apply limit
        limited_projections = projections_list[:limit]
        
        return {
            'message': f"Consensus projections for {'week ' + str(week) if week else 'season'} {season}",
            'filters': {
                'week': week,
                'season': season,
                'position': position,
                'limit': limit
            },
            'summary_stats': summary_stats,
            'projections': limited_projections
        }
        
    except Exception as e:
        logger.error(f"Failed to get consensus projections: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/consensus/test")
async def test_consensus_projections(
    position: str = Query("QB", description="Position to test consensus for"),
    limit: int = Query(10, description="Number of players to return"),
    season: str = Query(settings.default_season, description="NFL season"),
    db: Session = Depends(get_db)
):
    """Test consensus projection aggregation"""
    
    try:
        from app.services.projection_aggregation_service import ProjectionAggregationService
        
        # Initialize aggregation service
        aggregation_service = ProjectionAggregationService(db)
        
        # Create consensus projections for specific position
        consensus_projections = await aggregation_service.create_consensus_projections(
            season=season,
            position_filter=position
        )
        
        # Get top players by fantasy points
        top_players = []
        for sleeper_id, consensus in list(consensus_projections.items())[:limit]:
            
            # Show individual projections for comparison
            individual_details = []
            for individual in consensus.individual_projections:
                individual_details.append({
                    'provider': individual.provider,
                    'weight': individual.weight,
                    'fantasy_points': individual.projections.get('fantasy_points', 0)
                })
            
            player_data = {
                'player_name': consensus.player_name,
                'team': consensus.team,
                'position': consensus.position,
                'consensus_fantasy_points': consensus.consensus_projections.get('fantasy_points', 0),
                'provider_count': consensus.provider_count,
                'individual_projections': individual_details,
                'consensus_projections': consensus.consensus_projections
            }
            top_players.append(player_data)
        
        # Sort by consensus fantasy points
        top_players.sort(key=lambda x: x['consensus_fantasy_points'], reverse=True)
        
        # Get summary stats
        summary_stats = aggregation_service.get_consensus_summary_stats(consensus_projections)
        
        return {
            'message': f'Consensus projection test completed for {position} position',
            'summary_stats': summary_stats,
            'top_players': top_players
        }
        
    except Exception as e:
        logger.error(f"Consensus projection test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/fantasypros/save")
async def save_fantasypros_projections(
    week: Optional[int] = Query(None, description="Week number for weekly projections"),
    season: str = Query(settings.default_season, description="NFL season"),
    db: Session = Depends(get_db)
):
    """Fetch and save FantasyPros projections to database"""
    
    try:
        # Initialize projection service
        projection_service = ProjectionService(db)
        
        # Save FantasyPros projections
        results = await projection_service.save_fantasypros_projections(
            week=week,
            season=season
        )

        # Invalidate consensus projection cache since we have new data
        from app.services.projection_aggregation_service import ProjectionAggregationService
        aggregation_service = ProjectionAggregationService(db)
        aggregation_service.invalidate_cache(week=week, season=season)

        # Cleanup
        await projection_service.close()

        return {
            'message': f"FantasyPros projections saved for {'week ' + str(week) if week else 'season'} {season}",
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Failed to save FantasyPros projections: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/consensus/rankings")
async def get_consensus_rankings(
    position: Optional[str] = Query(None, description="Position filter (QB, RB, WR, TE, K, DEF)"),
    week: Optional[int] = Query(None, description="Week number (omit for season-long)"),
    season: str = Query(settings.default_season, description="NFL season"),
    limit: int = Query(100, description="Maximum players to return"),
    min_points: float = Query(0.0, description="Minimum projected points filter"),
    db: Session = Depends(get_db)
):
    """Get consensus projection rankings for UI consumption"""
    
    try:
        from app.services.projection_aggregation_service import ProjectionAggregationService
        
        # Initialize aggregation service
        aggregation_service = ProjectionAggregationService(db)
        
        # Create consensus projections
        consensus_projections = await aggregation_service.create_consensus_projections(
            week=week,
            season=season,
            position_filter=position
        )
        
        # Convert to ranked list
        rankings = []
        for sleeper_id, consensus in consensus_projections.items():
            fantasy_points = consensus.consensus_projections.get('fantasy_points', 0)
            
            # Apply minimum points filter
            if fantasy_points < min_points:
                continue
            
            player_ranking = {
                'sleeper_id': sleeper_id,
                'player_name': consensus.player_name,
                'team': consensus.team,
                'position': consensus.position,
                'projected_points': round(fantasy_points, 2),
                'projections': {
                    'fantasy_points': round(fantasy_points, 2),
                    'passing_yards': round(consensus.consensus_projections.get('passing_yards', 0), 1),
                    'passing_tds': round(consensus.consensus_projections.get('passing_tds', 0), 1),
                    'rushing_yards': round(consensus.consensus_projections.get('rushing_yards', 0), 1),
                    'rushing_tds': round(consensus.consensus_projections.get('rushing_tds', 0), 1),
                    'receiving_yards': round(consensus.consensus_projections.get('receiving_yards', 0), 1),
                    'receiving_tds': round(consensus.consensus_projections.get('receiving_tds', 0), 1),
                    'receptions': round(consensus.consensus_projections.get('receptions', 0), 1),
                },
                'provider_count': consensus.provider_count,
                'confidence': round(consensus.total_weight, 2)
            }
            rankings.append(player_ranking)
        
        # Sort by projected points descending
        rankings.sort(key=lambda x: x['projected_points'], reverse=True)
        
        # Apply limit
        limited_rankings = rankings[:limit]
        
        # Add ranking positions
        for i, player in enumerate(limited_rankings, 1):
            player['rank'] = i
        
        # Get summary stats
        summary_stats = aggregation_service.get_consensus_summary_stats(consensus_projections)
        
        return {
            'success': True,
            'data': {
                'rankings': limited_rankings,
                'metadata': {
                    'total_players': len(rankings),
                    'shown_players': len(limited_rankings),
                    'filters': {
                        'position': position,
                        'week': week,
                        'season': season,
                        'min_points': min_points,
                        'limit': limit
                    },
                    'summary_stats': summary_stats,
                    'generated_at': datetime.now().isoformat()
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get consensus rankings: {e}")
        raise HTTPException(status_code=500, detail=str(e))