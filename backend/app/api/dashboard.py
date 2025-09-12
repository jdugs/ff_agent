from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.database import get_db
from app.models.players import Player, NFLTeam
from app.models.rankings import Ranking
from app.models.sources import Source
from app.models.sleeper import SleeperLeague, SleeperPlayer, SleeperRoster, SleeperPlayerStats
from app.config import settings
from pydantic import BaseModel
from typing import List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()

class DashboardStats(BaseModel):
    total_players: int
    total_sources: int
    total_rankings: int
    active_sources: int
    sleeper_leagues: int
    sleeper_players: int

class TopPlayer(BaseModel):
    player_id: str
    name: str
    position: str
    team: str
    avg_rank: float
    ranking_count: int

class SleeperLeagueStats(BaseModel):
    league_id: str
    league_name: str
    season: str
    total_rosters: int
    last_synced: str

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get basic dashboard statistics including Sleeper data"""
    total_players = db.query(Player).count()
    total_sources = db.query(Source).count()
    total_rankings = db.query(Ranking).count()
    active_sources = db.query(Source).filter(Source.is_active == True).count()
    sleeper_leagues = db.query(SleeperLeague).count()
    sleeper_players = db.query(SleeperPlayer).count()
    
    return DashboardStats(
        total_players=total_players,
        total_sources=total_sources,
        total_rankings=total_rankings,
        active_sources=active_sources,
        sleeper_leagues=sleeper_leagues,
        sleeper_players=sleeper_players
    )

@router.get("/sleeper/leagues", response_model=List[SleeperLeagueStats])
async def get_sleeper_leagues(db: Session = Depends(get_db)):
    """Get all synced Sleeper leagues"""
    leagues = db.query(SleeperLeague).all()
    return [
        SleeperLeagueStats(
            league_id=league.league_id,
            league_name=league.league_name or "Unknown League",
            season=league.season,
            total_rosters=league.total_rosters or 0,
            last_synced=league.last_synced.strftime("%Y-%m-%d %H:%M") if league.last_synced else "Never"
        ) for league in leagues
    ]

@router.get("/top-players", response_model=List[TopPlayer])
async def get_top_players(
    position: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get top players by average ranking"""
    query = db.query(
        Player.player_id,
        Player.name,
        Player.position,
        Player.nfl_team,
        func.avg(Ranking.position_rank).label('avg_rank'),
        func.count(Ranking.ranking_id).label('ranking_count')
    ).join(Ranking).join(NFLTeam, Player.nfl_team == NFLTeam.team_code)
    
    if position:
        query = query.filter(Player.position == position.upper())
    
    top_players = query.group_by(
        Player.player_id, Player.name, Player.position, Player.nfl_team
    ).having(func.count(Ranking.ranking_id) >= 3).order_by(
        func.avg(Ranking.position_rank)
    ).limit(limit).all()
    
    return [
        TopPlayer(
            player_id=p.player_id,
            name=p.name,
            position=p.position,
            team=p.nfl_team,
            avg_rank=float(p.avg_rank),
            ranking_count=p.ranking_count
        ) for p in top_players
    ]

@router.get("/roster")
async def get_roster_dashboard(
    league_id: str = Query(..., description="Sleeper league ID"),
    owner_id: Optional[str] = Query(None, description="Sleeper owner ID (if not provided, uses default from config)"),
    week: Optional[int] = Query(None, description="Week number (omit for season-long)"),
    season: str = Query(settings.default_season, description="NFL season"),
    include_bench: bool = Query(True, description="Include bench players"),
    include_stats: bool = Query(True, description="Include actual player stats"),
    include_news: bool = Query(False, description="Include player news alerts (future)"),
    include_photos: bool = Query(False, description="Include player photo URLs (future)"),
    db: Session = Depends(get_db)
):
    """Get comprehensive roster dashboard with all player data for UI display"""
    
    try:
        from app.services.projection_aggregation_service import ProjectionAggregationService
        
        # Use default owner_id from config if not provided
        if not owner_id:
            owner_id = settings.sleeper_user_id
        
        # Get roster data from database
        roster = db.query(SleeperRoster).filter(
            SleeperRoster.league_id == league_id,
            SleeperRoster.owner_id == owner_id
        ).first()
        
        if not roster:
            raise HTTPException(
                status_code=404, 
                detail=f"Roster not found for owner {owner_id} in league {league_id}"
            )
        
        # Extract player IDs from roster
        all_player_ids = roster.player_ids or []
        starter_ids = roster.starters or []
        
        if not all_player_ids:
            return {
                'success': True,
                'data': {
                    'roster_summary': {
                        'league_id': league_id,
                        'owner_id': owner_id,
                        'total_players': 0,
                        'starters_count': 0,
                        'bench_count': 0
                    },
                    'lineup': {
                        'starters': [],
                        'bench': []
                    },
                    'metadata': {
                        'week': week,
                        'season': season,
                        'generated_at': datetime.now().isoformat()
                    }
                }
            }
        
        # Get player details for all roster players
        roster_players = db.query(SleeperPlayer).filter(
            SleeperPlayer.sleeper_player_id.in_(all_player_ids)
        ).all()
        
        # Create mapping of sleeper_id -> player for quick lookup
        player_map = {p.sleeper_player_id: p for p in roster_players}
        
        # Get projections for the week/season
        aggregation_service = ProjectionAggregationService(db)
        consensus_projections = await aggregation_service.create_consensus_projections(
            week=week,
            season=season
        )
        
        # Get actual stats if requested and we have a specific week
        stats_map = {}
        if include_stats and week:
            stats_query = db.query(SleeperPlayerStats).filter(
                SleeperPlayerStats.sleeper_player_id.in_(all_player_ids),
                SleeperPlayerStats.week == week,
                SleeperPlayerStats.season == season
            ).all()
            stats_map = {s.sleeper_player_id: s for s in stats_query}
        
        # Build comprehensive player data
        def build_player_dashboard_data(sleeper_id: str, is_starter: bool = False):
            player = player_map.get(sleeper_id)
            if not player:
                return None
            
            # Base player information
            player_data = {
                'sleeper_id': sleeper_id,
                'player_name': player.full_name or 'Unknown',
                'team': player.team or '',
                'position': player.position or '',
                'is_starter': is_starter,
                
                # Core player details
                'player_details': {
                    'age': player.age,
                    'height': player.height,
                    'weight': player.weight,
                    'college': player.college,
                    'years_exp': player.years_exp,
                    'status': str(player.status) if player.status else 'Active',
                    'fantasy_positions': player.fantasy_positions
                },
                
                # External IDs for future integrations
                'external_ids': {
                    'espn_id': player.espn_id,
                    'rotowire_id': player.rotowire_id,
                    'fantasy_data_id': player.fantasy_data_id,
                    'yahoo_id': player.yahoo_id,
                    'stats_id': player.stats_id
                }
            }
            
            # Add projections data
            consensus = consensus_projections.get(sleeper_id)
            if consensus:
                fantasy_points = consensus.consensus_projections.get('fantasy_points', 0)
                player_data['projections'] = {
                    'fantasy_points': round(fantasy_points, 2),
                    'passing': {
                        'yards': round(consensus.consensus_projections.get('passing_yards', 0), 1),
                        'touchdowns': round(consensus.consensus_projections.get('passing_tds', 0), 1),
                        'interceptions': round(consensus.consensus_projections.get('passing_ints', 0), 1)
                    },
                    'rushing': {
                        'yards': round(consensus.consensus_projections.get('rushing_yards', 0), 1),
                        'touchdowns': round(consensus.consensus_projections.get('rushing_tds', 0), 1)
                    },
                    'receiving': {
                        'yards': round(consensus.consensus_projections.get('receiving_yards', 0), 1),
                        'touchdowns': round(consensus.consensus_projections.get('receiving_tds', 0), 1),
                        'receptions': round(consensus.consensus_projections.get('receptions', 0), 1)
                    },
                    'meta': {
                        'provider_count': consensus.provider_count,
                        'confidence_score': round(consensus.total_weight, 2),
                        'last_updated': datetime.now().isoformat()
                    }
                }
            else:
                player_data['projections'] = None
            
            # Add actual stats if available and requested
            if include_stats and week:
                stats = stats_map.get(sleeper_id)
                if stats:
                    player_data['actual_stats'] = {
                        'fantasy_points': {
                            'ppr': float(stats.fantasy_points_ppr or 0),
                            'standard': float(stats.fantasy_points_standard or 0),
                            'half_ppr': float(stats.fantasy_points_half_ppr or 0)
                        },
                        'passing': {
                            'yards': stats.pass_yds or 0,
                            'touchdowns': stats.pass_tds or 0,
                            'interceptions': stats.pass_int or 0,
                            'attempts': stats.pass_att or 0,
                            'completions': stats.pass_cmp or 0
                        },
                        'rushing': {
                            'yards': stats.rush_yds or 0,
                            'touchdowns': stats.rush_tds or 0,
                            'attempts': stats.rush_att or 0
                        },
                        'receiving': {
                            'yards': stats.rec_yds or 0,
                            'touchdowns': stats.rec_tds or 0,
                            'receptions': stats.rec or 0,
                            'targets': stats.rec_tgt or 0
                        },
                        # Performance comparison (actual vs projected)
                        'performance': {
                            'vs_projection': None  # Will calculate if both exist
                        }
                    }
                    
                    # Calculate performance vs projection
                    if player_data['projections']:
                        projected_pts = player_data['projections']['fantasy_points']
                        actual_pts = player_data['actual_stats']['fantasy_points']['ppr']
                        if projected_pts > 0:
                            performance_pct = ((actual_pts - projected_pts) / projected_pts) * 100
                            player_data['actual_stats']['performance']['vs_projection'] = round(performance_pct, 1)
                else:
                    player_data['actual_stats'] = None
            else:
                player_data['actual_stats'] = None
            
            # Placeholder for future features
            if include_news:
                player_data['news_alerts'] = []  # Future: Recent news/injury updates
            
            if include_photos:
                player_data['media'] = {
                    'headshot_url': None,  # Future: Player photo URL
                    'team_logo_url': None  # Future: Team logo URL
                }
            
            return player_data
        
        # Build starters list
        starters = []
        for sleeper_id in starter_ids:
            player_data = build_player_dashboard_data(sleeper_id, is_starter=True)
            if player_data:
                starters.append(player_data)
        
        # Build bench list (if requested)
        bench = []
        if include_bench:
            bench_ids = [pid for pid in all_player_ids if pid not in starter_ids]
            for sleeper_id in bench_ids:
                player_data = build_player_dashboard_data(sleeper_id, is_starter=False)
                if player_data:
                    bench.append(player_data)
        
        # Sort by projected points (descending)
        starters.sort(key=lambda x: x['projections']['fantasy_points'] if x['projections'] else 0, reverse=True)
        bench.sort(key=lambda x: x['projections']['fantasy_points'] if x['projections'] else 0, reverse=True)
        
        # Calculate roster summary stats
        total_projected = sum(p['projections']['fantasy_points'] if p['projections'] else 0 for p in starters)
        total_actual = sum(
            p['actual_stats']['fantasy_points']['ppr'] if p.get('actual_stats') else 0 
            for p in starters
        ) if include_stats else None
        
        return {
            'success': True,
            'data': {
                'roster_summary': {
                    'league_id': league_id,
                    'owner_id': owner_id,
                    'total_players': len(starters) + len(bench),
                    'starters_count': len(starters),
                    'bench_count': len(bench),
                    'team_record': {
                        'wins': roster.wins or 0,
                        'losses': roster.losses or 0,
                        'ties': roster.ties or 0,
                        'points_for': float(roster.fpts or 0),
                        'points_against': float(roster.fpts_against or 0)
                    },
                    'projected_points_total': round(total_projected, 2),
                    'actual_points_total': round(total_actual, 2) if total_actual else None,
                    'performance_vs_projection': None  # Calculate if both exist
                },
                'lineup': {
                    'starters': starters,
                    'bench': bench if include_bench else []
                },
                'quick_stats': {
                    'top_performer': max(starters, key=lambda x: x['projections']['fantasy_points'] if x['projections'] else 0) if starters else None,
                    'positions_summary': {
                        pos: len([p for p in starters if p['position'] == pos])
                        for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'DEF']
                    }
                },
                'metadata': {
                    'week': week,
                    'season': season,
                    'data_includes': {
                        'projections': True,
                        'actual_stats': include_stats and week is not None,
                        'bench_players': include_bench,
                        'news_alerts': include_news,
                        'player_photos': include_photos
                    },
                    'generated_at': datetime.now().isoformat(),
                    'last_roster_sync': roster.last_synced.isoformat() if roster.last_synced else None
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get roster dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))