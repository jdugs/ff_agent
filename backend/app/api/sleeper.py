from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from app.config import settings
from app.database import get_db
from app.services.sleeper_service import SleeperService
from app.models.sleeper import SleeperLeague, SleeperRoster, SleeperPlayer
from pydantic import BaseModel

router = APIRouter()

class UserSearchResponse(BaseModel):
    user_id: str
    username: str
    display_name: Optional[str] = None
    avatar: Optional[str] = None

class LeagueResponse(BaseModel):
    league_id: str
    league_name: str
    season: str
    status: str
    total_rosters: int
    
    class Config:
        from_attributes = True

class RosterPlayerResponse(BaseModel):
    sleeper_id: str
    name: Optional[str] = None
    position: Optional[str] = None
    team: Optional[str] = None
    is_starter: bool = False

class RosterResponse(BaseModel):
    roster_id: int
    owner_id: Optional[str] = None
    wins: int
    losses: int
    ties: int
    fpts: float
    players: List[RosterPlayerResponse]
    
    class Config:
        from_attributes = True

@router.get("/user/search/{username}", response_model=UserSearchResponse)
async def search_user(username: str, db: Session = Depends(get_db)):
    """Find a Sleeper user by username"""
    service = SleeperService(db)
    try:
        user = await service.find_user_by_username(username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return UserSearchResponse(
            user_id=user['user_id'],
            username=user['username'],
            display_name=user.get('display_name'),
            avatar=user.get('avatar')
        )
    finally:
        await service.close()

@router.post("/user/{user_id}/sync")
async def sync_user_leagues(
    user_id: str, 
    background_tasks: BackgroundTasks,
    season: str = settings.default_season,
    db: Session = Depends(get_db)
):
    """Sync all leagues for a user"""
    
    async def sync_task():
        service = SleeperService(db)
        try:
            leagues = await service.sync_user_leagues(user_id, season)
            return {"synced_leagues": len(leagues)}
        finally:
            await service.close()
    
    background_tasks.add_task(sync_task)
    return {"message": "Sync started", "user_id": user_id}

@router.get("/user/{user_id}/leagues", response_model=List[LeagueResponse])
async def get_user_leagues(user_id: str, db: Session = Depends(get_db)):
    """Get all synced leagues for a user"""
    leagues = db.query(SleeperLeague).filter(SleeperLeague.user_id == user_id).all()
    return leagues

@router.post("/league/{league_id}/sync")
async def sync_league(
    league_id: str,
    background_tasks: BackgroundTasks,
    user_id: str,
    db: Session = Depends(get_db)
):
    """Fully sync a league (rosters, matchups, etc.)"""
    
    async def sync_task():
        service = SleeperService(db)
        try:
            league = await service.sync_league_full(league_id, user_id)
            return {"synced": league is not None}
        finally:
            await service.close()
    
    background_tasks.add_task(sync_task)
    return {"message": "League sync started", "league_id": league_id}

@router.get("/league/{league_id}", response_model=LeagueResponse)
async def get_league(league_id: str, db: Session = Depends(get_db)):
    """Get league information"""
    league = db.query(SleeperLeague).filter(SleeperLeague.league_id == league_id).first()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    return league

@router.get("/league/{league_id}/rosters", response_model=List[RosterResponse])
async def get_league_rosters(league_id: str, db: Session = Depends(get_db)):
    """Get all rosters in a league with player details"""
    service = SleeperService(db)
    
    rosters = db.query(SleeperRoster).filter(SleeperRoster.league_id == league_id).all()
    
    result = []
    for roster in rosters:
        # Get player details
        players = []
        if roster.player_ids:
            player_details = service.player_mapper.get_sleeper_players_for_roster(roster.player_ids)
            starters = roster.starters or []
            
            for player_detail in player_details:
                sleeper_player = player_detail['sleeper_player']
                players.append(RosterPlayerResponse(
                    sleeper_id=player_detail['sleeper_id'],
                    name=sleeper_player.full_name if sleeper_player else None,
                    position=sleeper_player.position if sleeper_player else None,
                    team=sleeper_player.team if sleeper_player else None,
                    is_starter=player_detail['sleeper_id'] in starters
                ))
        
        result.append(RosterResponse(
            roster_id=roster.roster_id,
            owner_id=roster.owner_id,
            wins=roster.wins,
            losses=roster.losses,
            ties=roster.ties,
            fpts=float(roster.fpts) if roster.fpts else 0.0,
            players=players
        ))
    
    return result

@router.get("/league/{league_id}/my-roster")
async def get_my_roster(
    league_id: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get the current user's roster in a league"""
    # First find the league to verify user is in it
    league = db.query(SleeperLeague).filter(
        SleeperLeague.league_id == league_id,
        SleeperLeague.user_id == user_id
    ).first()
    
    if not league:
        raise HTTPException(status_code=404, detail="League not found or user not in league")
    
    # Find user's roster
    roster = db.query(SleeperRoster).filter(
        SleeperRoster.league_id == league_id,
        SleeperRoster.owner_id == user_id
    ).first()
    
    if not roster:
        raise HTTPException(status_code=404, detail="Roster not found")
    
    # Get player details
    service = SleeperService(db)
    players = []
    if roster.player_ids:
        player_details = service.player_mapper.get_sleeper_players_for_roster(roster.player_ids)
        starters = roster.starters or []
        
        for player_detail in player_details:
            sleeper_player = player_detail['sleeper_player']
            our_player = player_detail['our_player']
            
            players.append({
                'sleeper_id': player_detail['sleeper_id'],
                'name': sleeper_player.full_name if sleeper_player else None,
                'position': sleeper_player.position if sleeper_player else None,
                'team': sleeper_player.team if sleeper_player else None,
                'is_starter': player_detail['sleeper_id'] in starters,
                'our_player_id': our_player.player_id if our_player else None,
                'has_rankings': our_player is not None
            })
    
    return {
        'roster_id': roster.roster_id,
        'owner_id': roster.owner_id,
        'record': f"{roster.wins}-{roster.losses}-{roster.ties}",
        'points_for': float(roster.fpts) if roster.fpts else 0.0,
        'players': players,
        'starters': len([p for p in players if p['is_starter']]),
        'bench': len([p for p in players if not p['is_starter']])
    }

@router.post("/sync/players")
async def sync_all_players(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Sync all NFL players from Sleeper"""
    
    async def sync_task():
        service = SleeperService(db)
        try:
            count = await service.sync_players()
            return {"synced_players": count}
        finally:
            await service.close()
    
    background_tasks.add_task(sync_task)
    return {"message": "Player sync started"}

@router.get("/seasons")
async def get_available_seasons():
    """Get list of available seasons"""
    return {
        "default_season": settings.default_season,
        "available_seasons": settings.available_seasons,
        "current_season": settings.default_season
    }

@router.get("/user/{user_id}/leagues/all-seasons")
async def get_user_leagues_all_seasons(user_id: str, db: Session = Depends(get_db)):
    """Get all synced leagues for a user across all seasons"""
    leagues = db.query(SleeperLeague).filter(
        SleeperLeague.user_id == user_id
    ).order_by(SleeperLeague.season.desc()).all()
    
    # Group by season
    by_season = {}
    for league in leagues:
        season = league.season
        if season not in by_season:
            by_season[season] = []
        by_season[season].append(league)
    
    return {
        "seasons": by_season,
        "total_leagues": len(leagues),
        "seasons_available": list(by_season.keys())
    }

@router.post("/user/{user_id}/sync-all-seasons")
async def sync_all_seasons(
    user_id: str,
    background_tasks: BackgroundTasks,
    seasons: List[str] = settings.available_seasons,
    db: Session = Depends(get_db)
):
    """Sync leagues for multiple seasons"""
    
    async def sync_multiple_seasons():
        service = SleeperService(db)
        try:
            results = {}
            for season in seasons:
                leagues = await service.sync_user_leagues(user_id, season)
                results[season] = len(leagues)
            return results
        finally:
            await service.close()
    
    background_tasks.add_task(sync_multiple_seasons)
    return {
        "message": "Multi-season sync started", 
        "user_id": user_id,
        "seasons": seasons
    }

@router.post("/sync/stats/{week}")
async def sync_player_stats(
    week: int,
    background_tasks: BackgroundTasks,
    season: str = settings.default_season,
    db: Session = Depends(get_db)
):
    """Sync player stats for a specific week"""
    
    async def sync_task():
        service = SleeperService(db)
        try:
            count = await service.sync_player_stats(week, season)
            return {"synced_stats": count}
        finally:
            await service.close()
    
    background_tasks.add_task(sync_task)
    return {"message": f"Stats sync started for week {week}", "week": week}

@router.post("/sync/projections/{week}")
async def sync_player_projections(
    week: int,
    background_tasks: BackgroundTasks,
    season: str = settings.default_season,
    db: Session = Depends(get_db)
):
    """Sync player projections for a specific week"""
    
    async def sync_task():
        service = SleeperService(db)
        try:
            count = await service.sync_player_projections(week, season)
            return {"synced_projections": count}
        finally:
            await service.close()
    
    background_tasks.add_task(sync_task)
    return {"message": f"Projections sync started for week {week}", "week": week}

@router.get("/player/{player_id}/stats")
async def get_player_stats(
    player_id: str,
    season: str = settings.default_season,
    season_type: str = "regular",
    db: Session = Depends(get_db)
):
    """Get individual player stats from Sleeper API"""
    service = SleeperService(db)
    try:
        stats = await service.client.get_player_stats_individual(player_id, season, season_type)
        if not stats:
            raise HTTPException(status_code=404, detail="Player stats not found")
        
        return {
            "player_id": player_id,
            "season": season,
            "season_type": season_type,
            "stats": stats
        }
    finally:
        await service.close()

@router.get("/league/{league_id}/matchups/{week}")
async def get_league_matchups(
    league_id: str,
    week: int,
    db: Session = Depends(get_db)
):
    """Get matchups for a specific week"""
    service = SleeperService(db)
    try:
        # First try to get from database
        from app.models.sleeper import SleeperMatchup
        matchups = db.query(SleeperMatchup).filter(
            SleeperMatchup.league_id == league_id,
            SleeperMatchup.week == week
        ).all()
        
        if not matchups:
            # Sync from API if not in database
            matchups = await service.sync_league_matchups(league_id, week)
        
        return [
            {
                'roster_id': matchup.roster_id,
                'matchup_id': matchup.matchup_id_sleeper,
                'points': float(matchup.points) if matchup.points else 0,
                'points_for': float(matchup.points_for) if matchup.points_for else 0,
                'starters': matchup.starters,
                'starters_points': matchup.starters_points,
                'players_points': matchup.players_points
            } for matchup in matchups
        ]
    finally:
        await service.close()

@router.get("/league/{league_id}/my-matchup/{week}")
async def get_my_matchup(
    league_id: str,
    week: int,
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get the current user's matchup for a specific week"""
    service = SleeperService(db)
    try:
        from app.models.sleeper import SleeperMatchup, SleeperRoster
        
        # Find user's roster
        my_roster = db.query(SleeperRoster).filter(
            SleeperRoster.league_id == league_id,
            SleeperRoster.owner_id == user_id
        ).first()
        
        if not my_roster:
            raise HTTPException(status_code=404, detail="Your roster not found")
        
        # Find user's matchup
        my_matchup = db.query(SleeperMatchup).filter(
            SleeperMatchup.league_id == league_id,
            SleeperMatchup.week == week,
            SleeperMatchup.roster_id == my_roster.roster_id
        ).first()
        
        if not my_matchup:
            # Try to sync matchups if not found
            await service.sync_league_matchups(league_id, week)
            my_matchup = db.query(SleeperMatchup).filter(
                SleeperMatchup.league_id == league_id,
                SleeperMatchup.week == week,
                SleeperMatchup.roster_id == my_roster.roster_id
            ).first()
        
        if not my_matchup:
            raise HTTPException(status_code=404, detail="Matchup not found")
        
        # Find opponent's matchup (same matchup_id_sleeper, different roster_id)
        opponent_matchup = db.query(SleeperMatchup).filter(
            SleeperMatchup.league_id == league_id,
            SleeperMatchup.week == week,
            SleeperMatchup.matchup_id_sleeper == my_matchup.matchup_id_sleeper,
            SleeperMatchup.roster_id != my_roster.roster_id
        ).first()
        
        # Get opponent roster info
        opponent_roster = None
        if opponent_matchup:
            opponent_roster = db.query(SleeperRoster).filter(
                SleeperRoster.league_id == league_id,
                SleeperRoster.roster_id == opponent_matchup.roster_id
            ).first()
        
        # Get projections using the same service as dashboard
        from app.services.projection_aggregation_service import ProjectionAggregationService
        aggregation_service = ProjectionAggregationService(db)
        consensus_projections = await aggregation_service.create_consensus_projections(
            week=week,
            season="2025"  # TODO: Make this configurable
        )
        
        # Get my player details with projections
        my_players = []
        if my_matchup.starters:
            for sleeper_id in my_matchup.starters:
                sleeper_player = db.query(SleeperPlayer).filter(
                    SleeperPlayer.sleeper_player_id == sleeper_id
                ).first()
                
                # Get consensus projection
                consensus = consensus_projections.get(sleeper_id)
                fantasy_points = consensus.consensus_projections.get('fantasy_points', 0) if consensus else 0
                
                my_players.append({
                    'sleeper_id': sleeper_id,
                    'player_name': sleeper_player.full_name if sleeper_player else None,
                    'position': sleeper_player.position if sleeper_player else None,
                    'team': sleeper_player.team if sleeper_player else None,
                    'projections': {
                        'fantasy_points': round(fantasy_points, 2)
                    } if fantasy_points > 0 else None
                })
        
        # Get opponent player details with projections
        opponent_players = []
        if opponent_matchup and opponent_matchup.starters:
            for sleeper_id in opponent_matchup.starters:
                sleeper_player = db.query(SleeperPlayer).filter(
                    SleeperPlayer.sleeper_player_id == sleeper_id
                ).first()
                
                # Get consensus projection
                consensus = consensus_projections.get(sleeper_id)
                fantasy_points = consensus.consensus_projections.get('fantasy_points', 0) if consensus else 0
                
                opponent_players.append({
                    'sleeper_id': sleeper_id,
                    'player_name': sleeper_player.full_name if sleeper_player else None,
                    'position': sleeper_player.position if sleeper_player else None,
                    'team': sleeper_player.team if sleeper_player else None,
                    'projections': {
                        'fantasy_points': round(fantasy_points, 2)
                    } if fantasy_points > 0 else None
                })
        
        return {
            'week': week,
            'my_roster': {
                'roster_id': my_roster.roster_id,
                'owner_id': my_roster.owner_id,
                'points': float(my_matchup.points) if my_matchup.points else 0,
                'record': f"{my_roster.wins}-{my_roster.losses}",
                'starters': my_matchup.starters,
                'starters_points': my_matchup.starters_points,
                'players': my_players,
                'projected_total': sum(p['projections']['fantasy_points'] for p in my_players if p['projections'])
            },
            'opponent_roster': {
                'roster_id': opponent_roster.roster_id if opponent_roster else None,
                'owner_id': opponent_roster.owner_id if opponent_roster else None,
                'points': float(opponent_matchup.points) if opponent_matchup and opponent_matchup.points else 0,
                'record': f"{opponent_roster.wins}-{opponent_roster.losses}" if opponent_roster else "0-0",
                'starters': opponent_matchup.starters if opponent_matchup else [],
                'starters_points': opponent_matchup.starters_points if opponent_matchup else [],
                'players': opponent_players,
                'projected_total': sum(p['projections']['fantasy_points'] for p in opponent_players if p['projections'])
            } if opponent_matchup and opponent_roster else None,
            'matchup_id': my_matchup.matchup_id_sleeper,
            'is_complete': my_matchup.points is not None and (opponent_matchup is None or opponent_matchup.points is not None)
        }
        
    finally:
        await service.close()