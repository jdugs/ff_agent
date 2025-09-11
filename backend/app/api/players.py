from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app.database import get_db
from app.models.players import Player, NFLTeam
from app.models.rankings import Ranking
from pydantic import BaseModel

router = APIRouter()

class PlayerResponse(BaseModel):
    player_id: str
    name: str
    position: str
    nfl_team: str
    bye_week: Optional[int] = None
    injury_status: Optional[str] = None
    
    class Config:
        from_attributes = True

class PlayerWithRankings(BaseModel):
    player_id: str
    name: str
    position: str
    nfl_team: str
    latest_ranking: Optional[int] = None
    latest_projection: Optional[float] = None
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[PlayerResponse])
async def get_players(
    position: Optional[str] = None,
    team: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get all players with optional filtering"""
    query = db.query(Player)
    
    if position:
        query = query.filter(Player.position == position.upper())
    if team:
        query = query.filter(Player.nfl_team == team.upper())
    
    players = query.limit(limit).all()
    return players

@router.get("/{player_id}", response_model=PlayerResponse)
async def get_player(player_id: str, db: Session = Depends(get_db)):
    """Get a specific player by ID"""
    player = db.query(Player).filter(Player.player_id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player

@router.get("/{player_id}/rankings")
async def get_player_rankings(
    player_id: str, 
    week: Optional[int] = None,
    year: int = 2024,
    db: Session = Depends(get_db)
):
    """Get rankings for a specific player"""
    query = db.query(Ranking).filter(
        Ranking.player_id == player_id,
        Ranking.year == year
    )
    
    if week:
        query = query.filter(Ranking.week == week)
    
    rankings = query.all()
    if not rankings:
        raise HTTPException(status_code=404, detail="No rankings found for this player")
    
    return rankings