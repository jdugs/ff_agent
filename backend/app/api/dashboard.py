from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.database import get_db
from app.models.players import Player, NFLTeam
from app.models.rankings import Ranking
from app.models.sources import Source
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class DashboardStats(BaseModel):
    total_players: int
    total_sources: int
    total_rankings: int
    active_sources: int

class TopPlayer(BaseModel):
    player_id: str
    name: str
    position: str
    team: str
    avg_rank: float
    ranking_count: int

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get basic dashboard statistics"""
    total_players = db.query(Player).count()
    total_sources = db.query(Source).count()
    total_rankings = db.query(Ranking).count()
    active_sources = db.query(Source).filter(Source.is_active == True).count()
    
    return DashboardStats(
        total_players=total_players,
        total_sources=total_sources,
        total_rankings=total_rankings,
        active_sources=active_sources
    )

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
