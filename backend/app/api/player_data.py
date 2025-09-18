from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.services.stats_service import StatsService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/stats/sync/{week}")
async def sync_player_stats(
    week: int,
    background_tasks: BackgroundTasks,
    season: str = settings.default_season,
    db: Session = Depends(get_db)
):
    """Sync player stats for a specific week"""

    async def sync_task():
        service = StatsService(db)
        try:
            count = await service.sync_player_stats(week, season)
            logger.info(f"Successfully synced {count} player stats for week {week}, season {season}")
            return {"synced_stats": count}
        except Exception as e:
            logger.error(f"Failed to sync player stats for week {week}: {e}")
            raise
        finally:
            await service.close()

    background_tasks.add_task(sync_task)
    return {
        "message": f"Player stats sync started for week {week}",
        "week": week,
        "season": season
    }

@router.post("/projections/sync/{week}")
async def sync_player_projections(
    week: int,
    background_tasks: BackgroundTasks,
    season: str = settings.default_season,
    db: Session = Depends(get_db)
):
    """Sync player projections for a specific week"""

    async def sync_task():
        service = StatsService(db)
        try:
            count = await service.sync_player_projections(week, season)

            # Invalidate consensus projection cache since we have new data
            from app.services.projection_aggregation_service import ProjectionAggregationService
            aggregation_service = ProjectionAggregationService(db)
            aggregation_service.invalidate_cache(week=week, season=season)

            logger.info(f"Successfully synced {count} player projections for week {week}, season {season}")
            return {"synced_projections": count}
        except Exception as e:
            logger.error(f"Failed to sync player projections for week {week}: {e}")
            raise
        finally:
            await service.close()

    background_tasks.add_task(sync_task)
    return {
        "message": f"Player projections sync started for week {week}",
        "week": week,
        "season": season
    }

@router.post("/sync/all/{week}")
async def sync_all_player_data(
    week: int,
    background_tasks: BackgroundTasks,
    season: str = settings.default_season,
    db: Session = Depends(get_db)
):
    """Sync both player stats and projections for a specific week"""

    async def sync_task():
        service = StatsService(db)
        try:
            # Sync stats first
            stats_count = await service.sync_player_stats(week, season)
            logger.info(f"Synced {stats_count} player stats for week {week}")

            # Then sync projections
            projections_count = await service.sync_player_projections(week, season)
            logger.info(f"Synced {projections_count} player projections for week {week}")

            # Invalidate consensus projection cache
            from app.services.projection_aggregation_service import ProjectionAggregationService
            aggregation_service = ProjectionAggregationService(db)
            aggregation_service.invalidate_cache(week=week, season=season)

            total_count = stats_count + projections_count
            logger.info(f"Successfully synced {total_count} total records for week {week}, season {season}")
            return {
                "synced_stats": stats_count,
                "synced_projections": projections_count,
                "total_synced": total_count
            }
        except Exception as e:
            logger.error(f"Failed to sync player data for week {week}: {e}")
            raise
        finally:
            await service.close()

    background_tasks.add_task(sync_task)
    return {
        "message": f"Complete player data sync started for week {week}",
        "week": week,
        "season": season
    }

@router.get("/stats/{player_id}")
async def get_player_stats(
    player_id: str,
    week: int = None,
    season: str = settings.default_season,
    db: Session = Depends(get_db)
):
    """Get player stats from the database"""
    from app.models.sleeper import PlayerStats

    query = db.query(PlayerStats).filter(
        PlayerStats.player_id == player_id,
        PlayerStats.season == season,
        PlayerStats.stat_type == 'actual'
    )

    if week:
        query = query.filter(PlayerStats.week == week)
        stats = query.first()
        if not stats:
            raise HTTPException(status_code=404, detail="Player stats not found")
        return {
            "player_id": player_id,
            "week": week,
            "season": season,
            "fantasy_points_ppr": float(stats.fantasy_points_ppr) if stats.fantasy_points_ppr else 0,
            "fantasy_points_standard": float(stats.fantasy_points_standard) if stats.fantasy_points_standard else 0,
            "fantasy_points_half_ppr": float(stats.fantasy_points_half_ppr) if stats.fantasy_points_half_ppr else 0,
            "stats": {
                "pass_yds": stats.pass_yds,
                "pass_tds": stats.pass_tds,
                "rush_yds": stats.rush_yds,
                "rush_tds": stats.rush_tds,
                "rec_yds": stats.rec_yds,
                "rec_tds": stats.rec_tds,
                "rec": stats.rec
            }
        }
    else:
        # Return all weeks for the season
        stats = query.order_by(PlayerStats.week.desc()).all()
        return {
            "player_id": player_id,
            "season": season,
            "weeks": [
                {
                    "week": s.week,
                    "fantasy_points_ppr": float(s.fantasy_points_ppr) if s.fantasy_points_ppr else 0,
                    "fantasy_points_standard": float(s.fantasy_points_standard) if s.fantasy_points_standard else 0,
                    "fantasy_points_half_ppr": float(s.fantasy_points_half_ppr) if s.fantasy_points_half_ppr else 0,
                } for s in stats
            ]
        }