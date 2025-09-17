from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.players import Player, NFLTeam
from app.models.rankings import Ranking
from app.models.sources import Source
from app.models.sleeper import SleeperLeague, SleeperPlayer, SleeperRoster, SleeperPlayerStats, SleeperMatchup
from app.config import settings
from app.services.nfl_schedule_service import NFLScheduleService
from app.services.fantasy_week_state_service import FantasyWeekStateService, FantasyWeekPhase
from app.utils.scoring import calculate_fantasy_points
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
        
        if not league_id:
            league_id = settings.sleeper_league_id
        
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

        # Get historical lineup from matchup data for the specific week
        all_player_ids = roster.player_ids or []
        starter_ids = []

        if week:
            # Get the historical lineup for this specific week
            matchup = db.query(SleeperMatchup).filter(
                SleeperMatchup.league_id == league_id,
                SleeperMatchup.roster_id == roster.roster_id,
                SleeperMatchup.week == week
            ).first()

            if matchup and matchup.starters:
                starter_ids = matchup.starters
            else:
                # Fallback to current roster starters if no historical data
                starter_ids = roster.starters or []
        else:
            # Use current roster starters if no week specified
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
        
        # Get league scoring settings for accurate calculations
        from app.models.sleeper import SleeperLeague
        league_data = db.query(SleeperLeague).filter(SleeperLeague.league_id == league_id).first()
        scoring_settings = league_data.scoring_settings if league_data else {}

        # Use shared scoring utility for consistent calculations

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
        async def build_player_dashboard_data(sleeper_id: str, is_starter: bool = False):
            player = player_map.get(sleeper_id)
            if not player:
                return None
            
            # Get game info for this player's team
            player_team = player.team or ''
            if not player_team:
                logger.warning(f"Player {player.full_name} ({sleeper_id}) has no team data")
            schedule_service = NFLScheduleService(db)
            opponent, game_time = schedule_service.get_opponent_and_time(player_team, week or 2)
            
            # Base player information
            player_data = {
                'sleeper_id': sleeper_id,
                'player_name': player.full_name or 'Unknown',
                'team': player.team or '',
                'position': player.position or '',
                'is_starter': is_starter,
                'opponent': opponent,
                'game_time': game_time,
                
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
                        'yards': round(consensus.consensus_projections.get('passing_yards', 0), 2),
                        'touchdowns': round(consensus.consensus_projections.get('passing_tds', 0), 2),
                        'interceptions': round(consensus.consensus_projections.get('passing_ints', 0), 2)
                    },
                    'rushing': {
                        'yards': round(consensus.consensus_projections.get('rushing_yards', 0), 2),
                        'touchdowns': round(consensus.consensus_projections.get('rushing_tds', 0), 2)
                    },
                    'receiving': {
                        'yards': round(consensus.consensus_projections.get('receiving_yards', 0), 2),
                        'touchdowns': round(consensus.consensus_projections.get('receiving_tds', 0), 2),
                        'receptions': round(consensus.consensus_projections.get('receptions', 0), 2)
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
                    # Calculate fantasy points using shared scoring utility
                    league_fantasy_points = calculate_fantasy_points(stats, scoring_settings, player.position)
                    
                    player_data['actual_stats'] = {
                        'fantasy_points': league_fantasy_points,
                        'passing': {
                            'yards': stats.pass_yds or 0,
                            'touchdowns': stats.pass_tds or 0,
                            'interceptions': stats.pass_ints or 0,
                            'attempts': stats.pass_att or 0,
                            'completions': stats.pass_cmp or 0,
                            'sacks_taken': getattr(stats, 'pass_sack', 0) or 0,
                            'two_point_conversions': getattr(stats, 'pass_2pt', 0) or 0
                        },
                        'rushing': {
                            'yards': stats.rush_yds or 0,
                            'touchdowns': stats.rush_tds or 0,
                            'attempts': stats.rush_att or 0,
                            'two_point_conversions': getattr(stats, 'rush_2pt', 0) or 0
                        },
                        'receiving': {
                            'yards': stats.rec_yds or 0,
                            'touchdowns': stats.rec_tds or 0,
                            'receptions': stats.rec or 0,
                            'targets': stats.rec_tgt or 0,
                            'two_point_conversions': getattr(stats, 'rec_2pt', 0) or 0
                        },
                        'kicking': {
                            'field_goals_made': getattr(stats, 'fgm', 0) or 0,
                            'field_goals_attempted': getattr(stats, 'fga', 0) or 0,
                            'extra_points_made': getattr(stats, 'xpm', 0) or 0,
                            'extra_points_attempted': getattr(stats, 'xpa', 0) or 0,
                            'extra_points_missed': getattr(stats, 'xpmiss', 0) or 0,
                            'field_goal_yards': getattr(stats, 'fgm_yds', 0) or 0,
                            'distance_breakdown': {
                                'fg_0_19': getattr(stats, 'fgm_0_19', 0) or 0,
                                'fg_20_29': getattr(stats, 'fgm_20_29', 0) or 0,
                                'fg_30_39': getattr(stats, 'fgm_30_39', 0) or 0,
                                'fg_40_49': getattr(stats, 'fgm_40_49', 0) or 0,
                                'fg_50_59': getattr(stats, 'fgm_50_59', 0) or 0,
                                'fg_60_plus': getattr(stats, 'fgm_60p', 0) or 0
                            },
                            'misses_breakdown': {
                                'miss_0_19': getattr(stats, 'fgmiss_0_19', 0) or 0,
                                'miss_20_29': getattr(stats, 'fgmiss_20_29', 0) or 0,
                                'miss_30_39': getattr(stats, 'fgmiss_30_39', 0) or 0,
                                'miss_40_49': getattr(stats, 'fgmiss_40_49', 0) or 0
                            }
                        },
                        'defense': {
                            'sacks': getattr(stats, 'def_sack', 0) or 0,
                            'interceptions': getattr(stats, 'def_int', 0) or 0,
                            'fumble_recoveries': getattr(stats, 'def_fumble_rec', 0) or 0,
                            'touchdowns': getattr(stats, 'def_td', 0) or 0,
                            'safeties': getattr(stats, 'def_safety', 0) or 0,
                            'blocked_kicks': getattr(stats, 'def_block_kick', 0) or 0,
                            'pass_deflections': getattr(stats, 'def_pass_def', 0) or 0,
                            'tackles_solo': getattr(stats, 'def_tackle_solo', 0) or 0,
                            'tackles_assist': getattr(stats, 'def_tackle_assist', 0) or 0,
                            'qb_hits': getattr(stats, 'def_qb_hit', 0) or 0,
                            'tackles_for_loss': getattr(stats, 'def_tfl', 0) or 0,
                            'fourth_down_stops': getattr(stats, 'def_4_and_stop', 0) or 0,
                            'points_allowed_tiers': {
                                'pts_0': getattr(stats, 'pts_allow_0', 0) or 0,
                                'pts_1_6': getattr(stats, 'pts_allow_1_6', 0) or 0,
                                'pts_7_13': getattr(stats, 'pts_allow_7_13', 0) or 0,
                                'pts_14_20': getattr(stats, 'pts_allow_14_20', 0) or 0,
                                'pts_21_27': getattr(stats, 'pts_allow_21_27', 0) or 0,
                                'pts_28_34': getattr(stats, 'pts_allow_28_34', 0) or 0,
                                'pts_35_plus': getattr(stats, 'pts_allow_35p', 0) or 0
                            },
                            'yards_allowed_tiers': {
                                'yds_0_100': getattr(stats, 'yds_allow_0_100', 0) or 0,
                                'yds_100_199': getattr(stats, 'yds_allow_100_199', 0) or 0,
                                'yds_200_299': getattr(stats, 'yds_allow_200_299', 0) or 0,
                                'yds_300_349': getattr(stats, 'yds_allow_300_349', 0) or 0,
                                'yds_350_399': getattr(stats, 'yds_allow_350_399', 0) or 0,
                                'yds_400_449': getattr(stats, 'yds_allow_400_449', 0) or 0,
                                'yds_450_499': getattr(stats, 'yds_allow_450_499', 0) or 0,
                                'yds_500_549': getattr(stats, 'yds_allow_500_549', 0) or 0,
                                'yds_550_plus': getattr(stats, 'yds_allow_550p', 0) or 0
                            },
                            # Continuous penalty values
                            'total_points_allowed': getattr(stats, 'pts_allow', 0) or 0,
                            'total_yards_allowed': getattr(stats, 'yds_allow', 0) or 0
                        },
                        'special_teams': {
                            'kick_return_yards': getattr(stats, 'kr_yd', 0) or 0,
                            'punt_return_yards': getattr(stats, 'pr_yd', 0) or 0,
                            'return_touchdowns': getattr(stats, 'st_td', 0) or 0,
                            'fumble_recoveries': getattr(stats, 'st_fum_rec', 0) or 0,
                            'forced_fumbles': getattr(stats, 'st_ff', 0) or 0
                        },
                        'miscellaneous': {
                            'fumbles': getattr(stats, 'fum', 0) or 0,
                            'fumbles_lost': getattr(stats, 'fum_lost', 0) or 0,
                            'forced_fumbles': getattr(stats, 'ff', 0) or 0,
                            'fumble_recovery_td': getattr(stats, 'fum_rec_td', 0) or 0,
                            'te_reception_bonus': getattr(stats, 'bonus_rec_te', 0) or 0,
                            'idp_tackles': getattr(stats, 'idp_tkl', 0) or 0
                        },
                        'kicking_debug': {
                            'fgm': getattr(stats, 'fgm', 0) or 0,
                            'fga': getattr(stats, 'fga', 0) or 0,
                            'xpm': getattr(stats, 'xpm', 0) or 0,
                            'xpa': getattr(stats, 'xpa', 0) or 0
                        },
                        # Performance comparison (actual vs projected)
                        'performance': {
                            'vs_projection': None  # Will calculate if both exist
                        }
                    }
                    
                    # Calculate performance vs projection
                    if player_data['projections']:
                        projected_pts = float(player_data['projections']['fantasy_points'])
                        actual_pts = float(player_data['actual_stats']['fantasy_points']['half_ppr'])
                        if projected_pts > 0:
                            performance_pct = ((actual_pts - projected_pts) / projected_pts) * 100
                            player_data['actual_stats']['performance']['vs_projection'] = round(performance_pct, 2)
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
            player_data = await build_player_dashboard_data(sleeper_id, is_starter=True)
            if player_data:
                starters.append(player_data)
        
        # Build bench list (if requested)
        bench = []
        if include_bench:
            bench_ids = [pid for pid in all_player_ids if pid not in starter_ids]
            for sleeper_id in bench_ids:
                player_data = await build_player_dashboard_data(sleeper_id, is_starter=False)
                if player_data:
                    bench.append(player_data)
        
        # Sort by projected points (descending)
        starters.sort(key=lambda x: x['projections']['fantasy_points'] if x['projections'] else 0, reverse=True)
        bench.sort(key=lambda x: x['projections']['fantasy_points'] if x['projections'] else 0, reverse=True)
        
        # Calculate roster summary stats
        total_projected = sum(p['projections']['fantasy_points'] if p['projections'] else 0 for p in starters)
        total_actual = sum(
            p['actual_stats']['fantasy_points']['half_ppr'] if p.get('actual_stats') else 0 
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
        import traceback
        logger.error(f"Failed to get roster dashboard: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/team-roster")
async def get_team_roster(
    league_id: str = Query(..., description="Sleeper league ID"),
    owner_id: str = Query(..., description="Sleeper owner ID"),
    week: Optional[int] = Query(None, description="Week number (omit for season-long)"),
    season: str = Query(settings.default_season, description="NFL season"),
    include_bench: bool = Query(True, description="Include bench players"),
    include_stats: bool = Query(True, description="Include actual player stats"),
    include_news: bool = Query(False, description="Include player news alerts (future)"),
    include_photos: bool = Query(False, description="Include player photo URLs (future)"),
    db: Session = Depends(get_db)
):
    """Get team roster data for any owner - unified endpoint for both user and opponent teams"""

    try:
        # This is essentially the same logic as the roster endpoint but parameterized by owner_id
        # This way both user team and opponent team can use the exact same data source and calculations
        return await get_roster_dashboard(
            league_id=league_id,
            owner_id=owner_id,
            week=week,
            season=season,
            include_bench=include_bench,
            include_stats=include_stats,
            include_news=include_news,
            include_photos=include_photos,
            db=db
        )
    except Exception as e:
        import traceback
        logger.error(f"Failed to get team roster: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/week-state")
async def get_fantasy_week_state():
    """Get current fantasy week phase and recommended dashboard configuration"""
    try:
        current_phase = FantasyWeekStateService.get_current_phase()
        phase_info = FantasyWeekStateService.get_phase_info(current_phase)
        next_phase, next_transition = FantasyWeekStateService.get_next_phase_transition()
        
        return {
            "current_phase": current_phase.value,
            "phase_info": phase_info,
            "next_phase": {
                "phase": next_phase.value,
                "transition_time": next_transition.isoformat(),
                "time_until_transition": str(next_transition - datetime.now(FantasyWeekStateService.ET))
            },
            "should_auto_refresh": FantasyWeekStateService.should_auto_refresh(current_phase),
            "recommended_sections": FantasyWeekStateService.get_recommended_sections(current_phase),
            "refresh_frequency_seconds": phase_info.get("refresh_frequency_seconds", 900),
            "timestamp": datetime.now(FantasyWeekStateService.ET).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get fantasy week state: {e}")
        raise HTTPException(status_code=500, detail=str(e))