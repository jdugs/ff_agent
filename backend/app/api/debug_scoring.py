"""
Debug scoring endpoint for testing and comparing fantasy point calculations
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Dict, Any, Optional
import logging

from app.database import get_db
from app.models.sleeper import PlayerStats
from app.models.players import Player
from app.models.leagues import League
from app.services.league_scoring_service import LeagueScoringService
from app.services.stat_mapping_service import StatMappingService, StatType
from app.utils.scoring import calculate_fantasy_points
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/scoring/debug/{league_id}")
async def debug_fantasy_scoring(
    league_id: str,
    player_id: Optional[str] = Query(None, description="Specific player to debug"),
    week: int = Query(3, description="Week to analyze"),
    season: str = Query(settings.default_season, description="Season"),
    stat_type: str = Query('actual', description="Stat type: actual or projection"),
    limit: int = Query(10, description="Number of players to analyze"),
    db: Session = Depends(get_db)
):
    """Debug fantasy point calculations vs expected values"""

    try:
        league_scoring_service = LeagueScoringService(db)
        stat_mapper = StatMappingService()

        # Get league info and scoring settings
        league = db.query(League).filter(League.league_id == league_id).first()
        if not league:
            raise HTTPException(status_code=404, detail="League not found")

        scoring_settings = league_scoring_service.get_league_scoring_settings(league_id)

        # Build query for player stats
        query = db.query(PlayerStats, Player).join(
            Player, PlayerStats.player_id == Player.player_id
        ).filter(
            and_(
                PlayerStats.week == week,
                PlayerStats.season == season,
                PlayerStats.stat_type == stat_type
            )
        )

        if player_id:
            query = query.filter(PlayerStats.player_id == player_id)

        # Get stats and limit results
        stats_with_players = query.limit(limit).all()

        if not stats_with_players:
            return {
                "message": f"No {stat_type} stats found for week {week}, season {season}",
                "league_id": league_id,
                "filters": {"week": week, "season": season, "stat_type": stat_type}
            }

        debug_results = []

        for player_stats, player in stats_with_players:
            # Get the raw stats from database
            raw_stats_dict = _extract_raw_stats_dict(player_stats)

            # Normalize stats using mapping service
            sleeper_stat_type = StatType.ACTUAL_STATS if stat_type == 'actual' else StatType.RAW_PROJECTIONS
            normalized_stats = stat_mapper.normalize_stats(
                stats=player_stats,
                stat_type=sleeper_stat_type,
                position=player.position
            )

            # Calculate fantasy points manually
            fantasy_points_dict = calculate_fantasy_points(
                stats=normalized_stats,
                scoring_settings=scoring_settings,
                player_position=player.position
            )

            # Get stored calculation if it exists
            stored_calculation = league_scoring_service.get_stored_fantasy_points(
                league_id=league_id,
                stat_id=player_stats.stat_id
            )

            # Prepare debug info
            debug_info = {
                "player": {
                    "player_id": player.player_id,
                    "name": player.full_name,
                    "position": player.position,
                    "team": player.team
                },
                "raw_stats_from_db": raw_stats_dict,
                "normalized_stats": normalized_stats,
                "scoring_settings_used": {k: v for k, v in scoring_settings.items() if k in [
                    'pass_yd', 'pass_td', 'pass_int', 'rush_yd', 'rush_td',
                    'rec_yd', 'rec_td', 'rec', 'fgm', 'xpm', 'def_sack', 'def_int'
                ]},
                "calculated_points": fantasy_points_dict,
                "stored_points": stored_calculation['fantasy_points'] if stored_calculation else None,
                "stored_breakdown": stored_calculation['scoring_breakdown'] if stored_calculation else None,
                "database_stored_points": {
                    "ppr": float(player_stats.fantasy_points_ppr) if player_stats.fantasy_points_ppr else None,
                    "standard": float(player_stats.fantasy_points_standard) if player_stats.fantasy_points_standard else None,
                    "half_ppr": float(player_stats.fantasy_points_half_ppr) if player_stats.fantasy_points_half_ppr else None
                }
            }

            debug_results.append(debug_info)

        return {
            "league_id": league_id,
            "league_name": league.league_name,
            "debug_info": {
                "week": week,
                "season": season,
                "stat_type": stat_type,
                "scoring_system": "sleeper_league_specific",
                "players_analyzed": len(debug_results)
            },
            "league_scoring_settings": scoring_settings,
            "players": debug_results
        }

    except Exception as e:
        logger.error(f"Debug scoring failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scoring/compare-sleeper/{league_id}")
async def compare_with_sleeper_api(
    league_id: str,
    week: int = Query(3, description="Week to compare"),
    season: str = Query(settings.default_season, description="Season"),
    db: Session = Depends(get_db)
):
    """Compare our calculations with raw Sleeper API data"""

    try:
        from app.integrations.sleeper_api import SleeperAPIClient

        league_scoring_service = LeagueScoringService(db)
        client = SleeperAPIClient()

        # Get raw Sleeper data
        sleeper_stats = await client.get_player_stats(week, season)
        sleeper_projections = await client.get_player_projections(week, season)

        # Get our database stats for comparison
        our_stats = db.query(PlayerStats, Player).join(
            Player, PlayerStats.player_id == Player.player_id
        ).filter(
            and_(
                PlayerStats.week == week,
                PlayerStats.season == season,
                PlayerStats.stat_type == 'actual'
            )
        ).limit(5).all()

        comparisons = []

        for player_stats, player in our_stats:
            sleeper_id = player.player_id
            sleeper_raw = sleeper_stats.get(sleeper_id, {})

            comparison = {
                "player": {
                    "id": sleeper_id,
                    "name": player.full_name,
                    "position": player.position
                },
                "sleeper_raw_stats": sleeper_raw,
                "our_database_stats": _extract_raw_stats_dict(player_stats),
                "field_mapping_issues": _identify_field_mapping_issues(sleeper_raw, player_stats)
            }

            comparisons.append(comparison)

        await client.close()

        return {
            "league_id": league_id,
            "week": week,
            "season": season,
            "sample_comparisons": comparisons,
            "sleeper_stats_sample": dict(list(sleeper_stats.items())[:3]),
            "sleeper_projections_sample": dict(list(sleeper_projections.items())[:3])
        }

    except Exception as e:
        logger.error(f"Sleeper comparison failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _extract_raw_stats_dict(player_stats: PlayerStats) -> Dict[str, Any]:
    """Extract all non-None stats from PlayerStats object"""
    stats_dict = {}

    # Define all possible stat fields
    stat_fields = [
        'pass_yds', 'pass_tds', 'pass_ints', 'pass_att', 'pass_cmp',
        'rush_yds', 'rush_tds', 'rush_att',
        'rec_yds', 'rec_tds', 'rec', 'rec_tgt',
        'fgm', 'fga', 'xpm', 'xpa', 'fgm_yds',
        'def_sack', 'def_int', 'def_fumble_rec', 'def_td', 'def_safety',
        'pts_allow_0', 'pts_allow_1_6', 'pts_allow_7_13', 'pts_allow_14_20',
        'fum_lost', 'pass_2pt', 'rush_2pt', 'rec_2pt'
    ]

    for field in stat_fields:
        value = getattr(player_stats, field, None)
        if value is not None:
            stats_dict[field] = float(value) if hasattr(value, '__float__') else value

    return stats_dict


def _identify_field_mapping_issues(sleeper_raw: Dict, our_stats: PlayerStats) -> Dict[str, str]:
    """Identify potential field mapping issues between Sleeper API and our database"""
    issues = {}

    # Check for common field name mismatches
    field_mappings = {
        'pass_yd': 'pass_yds',
        'pass_td': 'pass_tds',
        'pass_int': 'pass_ints',
        'rush_yd': 'rush_yds',
        'rush_td': 'rush_tds',
        'rec_yd': 'rec_yds',
        'rec_td': 'rec_tds'
    }

    for sleeper_field, our_field in field_mappings.items():
        sleeper_value = sleeper_raw.get(sleeper_field)
        our_value = getattr(our_stats, our_field, None)

        if sleeper_value is not None and our_value is None:
            issues[sleeper_field] = f"Sleeper has {sleeper_field}={sleeper_value} but our {our_field} is None"
        elif sleeper_value != our_value and sleeper_value is not None and our_value is not None:
            issues[sleeper_field] = f"Value mismatch: Sleeper={sleeper_value}, Ours={our_value}"

    return issues


@router.post("/fantasy-points/recalculate/{league_id}")
async def recalculate_fantasy_points(
    league_id: str,
    week: Optional[int] = Query(None, description="Specific week to recalculate (all weeks if not provided)"),
    season: str = Query(settings.default_season, description="Season"),
    stat_type: str = Query("actual", description="Stat type: 'actual' or 'projection'"),
    db: Session = Depends(get_db)
):
    """
    Recalculate fantasy points for all players in a league for specified criteria
    Forces recalculation with updated scoring rules
    """
    try:
        # Validate league exists
        league = db.query(League).filter(League.league_id == league_id).first()
        if not league:
            raise HTTPException(status_code=404, detail=f"League {league_id} not found")

        # Initialize scoring service
        scoring_service = LeagueScoringService(db)

        # Build query for stats to recalculate
        query = db.query(PlayerStats).filter(
            PlayerStats.season == season,
            PlayerStats.stat_type == stat_type
        )

        if week is not None:
            query = query.filter(PlayerStats.week == week)

        stats_list = query.all()

        if not stats_list:
            return {
                "league_id": league_id,
                "league_name": league.league_name,
                "recalculation_summary": {
                    "total_stats_found": 0,
                    "successfully_recalculated": 0,
                    "failed": 0,
                    "criteria": {
                        "week": week,
                        "season": season,
                        "stat_type": stat_type
                    }
                },
                "message": "No stats found matching criteria"
            }

        # Recalculate fantasy points
        successful_count = 0
        failed_count = 0
        failed_details = []

        for stat in stats_list:
            try:
                result = scoring_service.calculate_and_store_fantasy_points(
                    league_id=league_id,
                    stat_id=stat.stat_id,
                    player_stats=stat,
                    force_recalculate=True
                )
                if result is not None:
                    successful_count += 1
                else:
                    failed_count += 1
                    failed_details.append(f"Player {stat.player_id}, Week {stat.week}: Calculation returned None")
            except Exception as e:
                failed_count += 1
                failed_details.append(f"Player {stat.player_id}, Week {stat.week}: {str(e)}")

        return {
            "league_id": league_id,
            "league_name": league.league_name,
            "recalculation_summary": {
                "total_stats_found": len(stats_list),
                "successfully_recalculated": successful_count,
                "failed": failed_count,
                "criteria": {
                    "week": week,
                    "season": season,
                    "stat_type": stat_type
                }
            },
            "failed_details": failed_details[:10] if failed_details else [],  # Limit to first 10 failures
            "message": f"Successfully recalculated {successful_count} fantasy point calculations"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fantasy points recalculation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))