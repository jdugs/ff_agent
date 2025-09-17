from typing import Dict, Optional, Tuple
from datetime import datetime
import requests
import logging
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session
from app.models.nfl_schedule import NFLSchedule

logger = logging.getLogger(__name__)

class NFLScheduleService:
    """Service for getting NFL schedule and opponent information"""
    
    # Mapping from Sleeper team abbreviations to ESPN team abbreviations
    TEAM_ABBREVIATION_MAP = {
        'WAS': 'WSH',  # Washington Commanders
        # Add other mappings as needed
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    async def sync_week_schedule(self, week: int, season: str = "2025") -> bool:
        """Sync schedule data for a specific week from ESPN API to database"""
        try:
            url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?week={week}&seasontype=2"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            synced_count = 0
            
            for event in data.get('events', []):
                competitors = event.get('competitions', [{}])[0].get('competitors', [])
                if len(competitors) != 2:
                    continue
                
                # Find home and away teams
                home_team = None
                away_team = None
                for comp in competitors:
                    if comp.get('homeAway') == 'home':
                        home_team = comp.get('team', {}).get('abbreviation')
                    else:
                        away_team = comp.get('team', {}).get('abbreviation')
                
                if not home_team or not away_team:
                    continue
                
                # Parse game time and convert to Eastern Time
                game_date = event.get('date')
                game_time = None
                time_str = "TBD"
                if game_date:
                    try:
                        # Parse UTC time and convert to Eastern Time
                        dt_utc = datetime.fromisoformat(game_date.replace('Z', '+00:00'))
                        game_time = dt_utc.astimezone(ZoneInfo('America/New_York'))
                        time_str = game_time.strftime("%a %-I:%M %p ET")
                    except Exception as e:
                        logger.warning(f"Failed to parse game time {game_date}: {e}")
                        time_str = "TBD"
                
                espn_event_id = event.get('id')
                
                # Save both teams to database
                for team, opponent, is_home in [(home_team, away_team, True), (away_team, home_team, False)]:
                    schedule_entry = self.db.query(NFLSchedule).filter(
                        NFLSchedule.season == season,
                        NFLSchedule.week == week,
                        NFLSchedule.team == team
                    ).first()
                    
                    if schedule_entry:
                        # Update existing
                        schedule_entry.opponent = opponent
                        schedule_entry.is_home = is_home
                        schedule_entry.game_time = game_time
                        schedule_entry.game_time_str = time_str
                        schedule_entry.espn_event_id = espn_event_id
                        schedule_entry.game_date_raw = game_date
                    else:
                        # Create new
                        schedule_entry = NFLSchedule(
                            season=season,
                            week=week,
                            team=team,
                            opponent=opponent,
                            is_home=is_home,
                            game_time=game_time,
                            game_time_str=time_str,
                            espn_event_id=espn_event_id,
                            game_date_raw=game_date
                        )
                        self.db.add(schedule_entry)
                    
                    synced_count += 1
            
            self.db.commit()
            logger.info(f"Synced {synced_count} schedule entries for week {week}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync NFL schedule for week {week}: {e}")
            self.db.rollback()
            return False
    
    def get_game_info(self, team: str, week: int = 2, season: str = "2025") -> Optional[Dict[str, str]]:
        """Get game information for a team in a specific week from database"""
        # Map Sleeper team abbreviation to ESPN abbreviation if needed
        espn_team = self.TEAM_ABBREVIATION_MAP.get(team, team)
        
        schedule_entry = self.db.query(NFLSchedule).filter(
            NFLSchedule.season == season,
            NFLSchedule.week == week,
            NFLSchedule.team == espn_team
        ).first()
        
        if schedule_entry:
            return {
                'opponent': f"{'vs' if schedule_entry.is_home else '@'} {schedule_entry.opponent}",
                'time': schedule_entry.game_time_str or "TBD",
                'date': schedule_entry.game_date_raw,
                'home': schedule_entry.is_home
            }
        
        return None
    
    def get_opponent_and_time(self, team: str, week: int = 2, season: str = "2025") -> Tuple[str, str]:
        """Get opponent and game time as a tuple for display from database"""
        if not team:
            logger.warning(f"Empty team provided for schedule lookup")
            return "vs ???", "TBD"
            
        game_info = self.get_game_info(team, week, season)
        if game_info:
            return game_info['opponent'], game_info['time']
        
        # Map Sleeper team abbreviation to ESPN abbreviation if needed
        espn_team = self.TEAM_ABBREVIATION_MAP.get(team, team)
        mapped_note = f" (mapped from {team})" if espn_team != team else ""
        logger.warning(f"No schedule found for team '{espn_team}'{mapped_note} in week {week}")
        return f"vs ???", "TBD"