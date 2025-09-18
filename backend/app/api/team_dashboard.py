from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func
from typing import List, Optional, Dict, Any
from app.database import get_db
from app.services.sleeper_service import SleeperService
from app.models.sleeper import SleeperPlayerProjections, PlayerStats, SleeperMatchup
from app.models.leagues import League
from app.models.rosters import Roster
from app.models.players import Player
from app.models.rankings import Ranking, PlayerProjection
from app.models.sources import Source
from app.models.news import NewsEvent
from pydantic import BaseModel
from datetime import datetime, timedelta

router = APIRouter()

class PlayerRankingData(BaseModel):
    source_name: str
    position_rank: Optional[int] = None
    overall_rank: Optional[int] = None
    projection: Optional[float] = None
    tier: Optional[int] = None
    confidence: str
    timestamp: datetime

class PlayerNewsData(BaseModel):
    title: str
    event_type: str
    severity: str
    description: Optional[str] = None
    timestamp: datetime
    source_name: str

class TeamPlayerData(BaseModel):
    # Player info
    sleeper_id: str
    name: str
    position: str
    team: str
    is_starter: bool
    
    # Rankings from multiple sources
    rankings: List[PlayerRankingData]
    consensus_rank: Optional[float] = None
    rank_trend: Optional[str] = None  # "up", "down", "stable"
    
    # Projections
    latest_projection: Optional[float] = None
    projection_range: Optional[Dict[str, float]] = None  # min, max, avg
    
    # News and alerts
    recent_news: List[PlayerNewsData]
    injury_status: Optional[str] = None
    red_flags: List[str]
    
    # Recommendations
    start_sit_recommendation: Optional[str] = None
    confidence_score: Optional[float] = None

class TeamDashboardResponse(BaseModel):
    # Team info
    league_id: str
    league_name: str
    team_record: str
    points_for: float
    league_rank: Optional[int] = None
    
    # Roster breakdown
    starters: List[TeamPlayerData]
    bench: List[TeamPlayerData]
    
    # Team insights
    team_summary: Dict[str, Any]
    weekly_outlook: Dict[str, Any]
    
    # Last updated
    last_synced: datetime

@router.get("/{league_id}/{user_id}", response_model=TeamDashboardResponse)
async def get_team_dashboard(
    league_id: str,
    user_id: str,
    week: Optional[int] = Query(None, description="NFL week (current week if not specified)"),
    year: int = Query(2025, description="NFL year"),
    db: Session = Depends(get_db)
):
    """Get comprehensive team dashboard with rankings, projections, and recommendations"""
    
    # Get league and verify user access
    league = db.query(League).filter(
        League.league_id == league_id,
        League.user_id == user_id
    ).first()
    
    if not league:
        raise HTTPException(status_code=404, detail="League not found or access denied")
    
    # Get user's roster using the sleeper_user_id (NOT the user_id)
    roster = db.query(Roster).filter(
        Roster.league_id == league_id,
        Roster.owner_id == league.sleeper_user_id  # Use sleeper_user_id here!
    ).first()
    
    if not roster:
        # Add debug info to the error
        all_owners = db.query(SleeperRoster.owner_id).filter(
            SleeperRoster.league_id == league_id
        ).all()
        owner_list = [o[0] for o in all_owners]
        
        raise HTTPException(
            status_code=404, 
            detail=f"Roster not found. League sleeper_user_id: {league.sleeper_user_id}, Available owner_ids: {owner_list}"
        )
    
    # Get current NFL week if not specified
    if not week:
        week = _get_current_nfl_week()
    
    # Process each player on the roster
    service = SleeperService(db)
    starters = []
    bench = []
    
    if roster.player_ids:
        starter_ids = roster.starters or []
        
        for player_id in roster.player_ids:
            player_data = await _get_player_dashboard_data(
                db, player_id, week, year, starter_ids
            )
            
            if player_data:
                if player_data.is_starter:
                    starters.append(player_data)
                else:
                    bench.append(player_data)
    
    # Generate team insights
    team_summary = _generate_team_summary(starters, bench)
    weekly_outlook = _generate_weekly_outlook(starters, week)
    
    # Calculate league rank (simplified)
    league_rank = _calculate_league_rank(db, league_id, roster.roster_id)
    
    return TeamDashboardResponse(
        league_id=league_id,
        league_name=league.league_name or "Unknown League",
        team_record=f"{roster.wins}-{roster.losses}-{roster.ties}",
        points_for=float(roster.fpts) if roster.fpts else 0.0,
        league_rank=league_rank,
        starters=starters,
        bench=bench,
        team_summary=team_summary,
        weekly_outlook=weekly_outlook,
        last_synced=roster.last_synced or datetime.now()
    )

async def _get_player_dashboard_data(
    db: Session, 
    player_id: str, 
    week: int, 
    year: int,
    starter_ids: List[str]
) -> Optional[TeamPlayerData]:
    """Get comprehensive data for a single player"""
    
    # Get Sleeper player info
    player = db.query(Player).filter(
        Player.player_id == player_id
    ).first()
    
    if not player:
        return None
    
    # Get latest stats (previous week)
    latest_stats = db.query(PlayerStats).filter(
        PlayerStats.player_id == player_id,
        PlayerStats.season == str(year),
        PlayerStats.stat_type == 'actual'
    ).order_by(desc(PlayerStats.week)).first()
    
    # Get projections for current week
    projections = db.query(SleeperPlayerProjections).filter(
        SleeperPlayerProjections.sleeper_player_id == player_id,
        SleeperPlayerProjections.week == week,
        SleeperPlayerProjections.season == str(year)
    ).first()
    
    # Calculate latest projection
    latest_projection = None
    if projections:
        latest_projection = float(projections.projected_points_ppr or 0)
    
    # Get last week's actual points
    last_week_points = None
    if latest_stats:
        last_week_points = float(latest_stats.fantasy_points_ppr or 0)
    
    return TeamPlayerData(
        sleeper_id=player_id,
        name=player.full_name or "Unknown Player",
        position=player.position or "UNKNOWN",
        team=player.team or "FA",
        is_starter=player_id in starter_ids,
        rankings=[],  # Still empty until we add ranking sources
        consensus_rank=None,
        rank_trend=None,
        latest_projection=latest_projection,
        projection_range=None,
        recent_news=[],
        injury_status=player.status if player.status != 'Active' else None,
        red_flags=[],
        start_sit_recommendation=None,
        confidence_score=None,
        last_week_points=last_week_points  # Add this field to the model
    )

def _generate_team_summary(starters: List[TeamPlayerData], bench: List[TeamPlayerData]) -> Dict[str, Any]:
    """Generate team summary insights"""
    
    total_players = len(starters) + len(bench)
    players_with_rankings = len([p for p in starters + bench if p.rankings])
    
    # Count red flags
    total_red_flags = sum(len(p.red_flags) for p in starters + bench)
    injured_starters = len([p for p in starters if p.injury_status])
    
    # Projection totals
    starter_projections = [p.latest_projection for p in starters if p.latest_projection]
    projected_total = sum(starter_projections) if starter_projections else None
    
    return {
        "total_players": total_players,
        "players_with_rankings": players_with_rankings,
        "ranking_coverage": f"{players_with_rankings}/{total_players}",
        "total_red_flags": total_red_flags,
        "injured_starters": injured_starters,
        "projected_points": projected_total,
        "team_health": "concerning" if injured_starters > 1 else "good" if injured_starters == 0 else "monitor"
    }

def _generate_weekly_outlook(starters: List[TeamPlayerData], week: int) -> Dict[str, Any]:
    """Generate weekly outlook and recommendations"""
    
    strong_starts = len([p for p in starters if p.start_sit_recommendation == "start"])
    flex_plays = len([p for p in starters if p.start_sit_recommendation == "flex"])
    concerning = len([p for p in starters if p.start_sit_recommendation == "sit"])
    
    # Calculate team confidence
    confidences = [p.confidence_score for p in starters if p.confidence_score]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
    
    outlook = "strong" if avg_confidence > 0.8 else "moderate" if avg_confidence > 0.6 else "concerning"
    
    return {
        "week": week,
        "outlook": outlook,
        "strong_starts": strong_starts,
        "flex_plays": flex_plays,
        "concerning_starts": concerning,
        "avg_confidence": round(avg_confidence, 2),
        "recommendations": [
            f"{strong_starts} confident starts",
            f"{flex_plays} flex decisions needed",
            f"{concerning} concerning starts" if concerning > 0 else "No major concerns"
        ]
    }

def _calculate_league_rank(db: Session, league_id: str, roster_id: int) -> Optional[int]:
    """Calculate current league ranking"""
    try:
        rosters = db.query(Roster).filter(
            Roster.league_id == league_id
        ).order_by(desc(Roster.fpts)).all()
        
        for i, roster in enumerate(rosters, 1):
            if roster.roster_id == roster_id:
                return i
        return None
    except:
        return None

def _get_current_nfl_week() -> int:
    """Get current NFL week (simplified)"""
    # This is a simplified version - in production you'd call the NFL API
    # For now, return a reasonable default
    from datetime import datetime
    current_date = datetime.now()
    
    # Rough estimate: NFL season starts around week 36 of the year
    week_of_year = current_date.isocalendar()[1]
    
    if week_of_year < 30:  # Early in year, likely playoffs or offseason
        return 1
    elif week_of_year > 52:  # Late in year
        return 18
    else:
        # Rough calculation for regular season
        nfl_week = max(1, min(18, week_of_year - 35))
        return nfl_week