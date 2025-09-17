from enum import Enum
from datetime import datetime, time, timedelta
from typing import Dict, Optional, Tuple
from zoneinfo import ZoneInfo
import logging

logger = logging.getLogger(__name__)

class FantasyWeekPhase(Enum):
    """Different phases of a fantasy football week"""
    
    # Tuesday - Wednesday: Post-waivers, planning phase
    PLANNING = "planning"
    
    # Thursday: Early games start, some action begins
    EARLY_GAMES = "early_games" 
    
    # Friday - Saturday: Preparation for main slate
    PRE_GAMES = "pre_games"
    
    # Sunday - Monday: Main games happening, active monitoring
    GAMES_ACTIVE = "games_active"
    
    # Tuesday early AM: Games over, waivers not processed yet
    POST_GAMES = "post_games"
    
    # Tuesday AM: Waivers processing
    WAIVERS_PROCESSING = "waivers_processing"

class FantasyWeekStateService:
    """Service to determine current fantasy week phase and recommended actions"""
    
    # Eastern Time Zone (NFL schedule reference)
    ET = ZoneInfo('America/New_York')
    
    # Key times in fantasy week (all in ET)
    WAIVER_PROCESS_TIME = time(3, 0)  # 3:00 AM ET Tuesday
    WAIVER_CUTOFF_TIME = time(2, 59)  # 2:59 AM ET Tuesday  
    THURSDAY_GAME_START = time(20, 15)  # 8:15 PM ET Thursday (typical)
    SUNDAY_EARLY_GAMES = time(13, 0)  # 1:00 PM ET Sunday
    SUNDAY_LATE_GAMES = time(16, 25)  # 4:25 PM ET Sunday  
    SUNDAY_NIGHT_GAME = time(20, 20)  # 8:20 PM ET Sunday
    MONDAY_NIGHT_GAME = time(20, 15)  # 8:15 PM ET Monday
    
    @classmethod
    def get_current_phase(cls, current_time: Optional[datetime] = None) -> FantasyWeekPhase:
        """Determine current fantasy week phase based on time"""
        if current_time is None:
            current_time = datetime.now(cls.ET)
        elif current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=cls.ET)
        else:
            current_time = current_time.astimezone(cls.ET)
        
        day_of_week = current_time.weekday()  # 0=Monday, 6=Sunday
        current_time_only = current_time.time()
        
        # Tuesday after waivers process (3 AM) through Wednesday
        if (day_of_week == 1 and current_time_only >= cls.WAIVER_PROCESS_TIME) or day_of_week == 2:
            return FantasyWeekPhase.PLANNING
            
        # Thursday games active
        elif day_of_week == 3 and current_time_only >= cls.THURSDAY_GAME_START:
            return FantasyWeekPhase.EARLY_GAMES
            
        # Thursday before games, Friday, Saturday  
        elif day_of_week == 3 and current_time_only < cls.THURSDAY_GAME_START:
            return FantasyWeekPhase.PRE_GAMES
        elif day_of_week in [4, 5]:  # Friday, Saturday
            return FantasyWeekPhase.PRE_GAMES
            
        # Sunday games active (1 PM - end of SNF)
        elif day_of_week == 6 and current_time_only >= cls.SUNDAY_EARLY_GAMES:
            return FantasyWeekPhase.GAMES_ACTIVE
            
        # Monday games active
        elif day_of_week == 0 and current_time_only >= cls.MONDAY_NIGHT_GAME:
            return FantasyWeekPhase.GAMES_ACTIVE
        elif day_of_week == 0 and current_time_only < cls.MONDAY_NIGHT_GAME:
            # Monday before MNF - could be games active if late Sunday games
            return FantasyWeekPhase.GAMES_ACTIVE
            
        # Tuesday before waivers process (post-games analysis time)
        elif day_of_week == 1 and current_time_only < cls.WAIVER_CUTOFF_TIME:
            return FantasyWeekPhase.POST_GAMES
            
        # Tuesday waiver processing window (2:59 AM - 3:00 AM)
        elif day_of_week == 1 and cls.WAIVER_CUTOFF_TIME <= current_time_only < cls.WAIVER_PROCESS_TIME:
            return FantasyWeekPhase.WAIVERS_PROCESSING
            
        # Sunday before games start
        elif day_of_week == 6 and current_time_only < cls.SUNDAY_EARLY_GAMES:
            return FantasyWeekPhase.PRE_GAMES
            
        # Default fallback
        else:
            return FantasyWeekPhase.PLANNING
    
    @classmethod
    def get_phase_info(cls, phase: FantasyWeekPhase) -> Dict:
        """Get detailed information about a fantasy week phase"""
        
        phase_configs = {
            FantasyWeekPhase.PLANNING: {
                "name": "Planning & Research",
                "description": "Post-waivers period for planning next week's lineup",
                "priority_actions": [
                    "Review waiver results",
                    "Analyze next week's matchups", 
                    "Research free agents",
                    "Plan potential trades",
                    "Read fantasy news and analysis"
                ],
                "refresh_frequency_seconds": 1800,  # 30 minutes
                "focus_areas": ["matchup_analysis", "free_agents", "news"],
                "urgency": "low"
            },
            
            FantasyWeekPhase.EARLY_GAMES: {
                "name": "Thursday Night Football", 
                "description": "Thursday games in progress",
                "priority_actions": [
                    "Monitor Thursday player performance",
                    "Track injuries from Thursday games",
                    "Adjust weekend lineup if needed",
                    "Last-minute waiver pickups before Sunday"
                ],
                "refresh_frequency_seconds": 300,  # 5 minutes
                "focus_areas": ["live_scores", "injury_updates", "lineup_decisions"],
                "urgency": "medium"
            },
            
            FantasyWeekPhase.PRE_GAMES: {
                "name": "Pre-Game Preparation",
                "description": "Final preparations before main slate",
                "priority_actions": [
                    "Set final lineup decisions",
                    "Check injury reports",
                    "Monitor weather conditions", 
                    "Last-minute pickups from waivers",
                    "Review start/sit recommendations"
                ],
                "refresh_frequency_seconds": 600,  # 10 minutes  
                "focus_areas": ["lineup_optimization", "injury_reports", "weather"],
                "urgency": "medium"
            },
            
            FantasyWeekPhase.GAMES_ACTIVE: {
                "name": "Games In Progress",
                "description": "Sunday/Monday games active - live monitoring", 
                "priority_actions": [
                    "Monitor live player scores",
                    "Track real-time matchup progress",
                    "Watch for injuries during games",
                    "Celebrate/commiserate performances",
                    "Plan for next week based on results"
                ],
                "refresh_frequency_seconds": 120,  # 2 minutes
                "focus_areas": ["live_scores", "real_time_analysis", "injury_tracking"],
                "urgency": "high"
            },
            
            FantasyWeekPhase.POST_GAMES: {
                "name": "Post-Game Analysis", 
                "description": "Games finished, analyze results before waivers",
                "priority_actions": [
                    "Analyze player performances", 
                    "Identify waiver wire targets",
                    "Review league standings",
                    "Plan waiver claims",
                    "Research breakout players"
                ],
                "refresh_frequency_seconds": 900,  # 15 minutes
                "focus_areas": ["performance_analysis", "waiver_targets", "standings"],
                "urgency": "medium"
            },
            
            FantasyWeekPhase.WAIVERS_PROCESSING: {
                "name": "Waivers Processing",
                "description": "Waiver claims being processed", 
                "priority_actions": [
                    "Wait for waiver results",
                    "Prepare backup plans if claims fail",
                    "Monitor league activity"
                ],
                "refresh_frequency_seconds": 180,  # 3 minutes
                "focus_areas": ["waiver_results"],
                "urgency": "medium"
            }
        }
        
        return phase_configs.get(phase, phase_configs[FantasyWeekPhase.PLANNING])
    
    @classmethod
    def get_next_phase_transition(cls, current_time: Optional[datetime] = None) -> Tuple[FantasyWeekPhase, datetime]:
        """Get the next phase and when it will occur"""
        if current_time is None:
            current_time = datetime.now(cls.ET)
        elif current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=cls.ET)
        else:
            current_time = current_time.astimezone(cls.ET)
        
        current_phase = cls.get_current_phase(current_time)
        
        # Calculate next transition based on current phase
        if current_phase == FantasyWeekPhase.PLANNING:
            # Next transition: Thursday game start
            days_until_thursday = (3 - current_time.weekday()) % 7
            if days_until_thursday == 0 and current_time.time() >= cls.THURSDAY_GAME_START:
                days_until_thursday = 7  # Next week's Thursday
            next_transition = current_time.replace(
                hour=cls.THURSDAY_GAME_START.hour,
                minute=cls.THURSDAY_GAME_START.minute,
                second=0,
                microsecond=0
            ) + timedelta(days=days_until_thursday)
            return FantasyWeekPhase.EARLY_GAMES, next_transition
            
        elif current_phase == FantasyWeekPhase.EARLY_GAMES:
            # Next transition: Sunday early games
            days_until_sunday = (6 - current_time.weekday()) % 7
            if days_until_sunday == 0:  # Already Sunday
                days_until_sunday = 7  # Next Sunday
            next_transition = current_time.replace(
                hour=cls.SUNDAY_EARLY_GAMES.hour,
                minute=cls.SUNDAY_EARLY_GAMES.minute,
                second=0,
                microsecond=0
            ) + timedelta(days=days_until_sunday)
            return FantasyWeekPhase.GAMES_ACTIVE, next_transition
            
        # Add more transition logic as needed...
        
        # Default: next Tuesday waiver processing
        days_until_tuesday = (1 - current_time.weekday()) % 7
        if days_until_tuesday == 0 and current_time.time() >= cls.WAIVER_PROCESS_TIME:
            days_until_tuesday = 7
        next_transition = current_time.replace(
            hour=cls.WAIVER_PROCESS_TIME.hour,
            minute=cls.WAIVER_PROCESS_TIME.minute,
            second=0,
            microsecond=0
        ) + timedelta(days=days_until_tuesday)
        return FantasyWeekPhase.PLANNING, next_transition
    
    @classmethod
    def should_auto_refresh(cls, phase: FantasyWeekPhase) -> bool:
        """Determine if dashboard should auto-refresh for this phase"""
        return phase in [
            FantasyWeekPhase.GAMES_ACTIVE,
            FantasyWeekPhase.EARLY_GAMES,
            FantasyWeekPhase.WAIVERS_PROCESSING
        ]
    
    @classmethod 
    def get_recommended_sections(cls, phase: FantasyWeekPhase) -> list:
        """Get recommended dashboard sections for current phase"""
        
        section_recommendations = {
            FantasyWeekPhase.PLANNING: [
                "matchup_preview",
                "free_agents", 
                "trade_analyzer",
                "news_feed",
                "league_standings"
            ],
            
            FantasyWeekPhase.EARLY_GAMES: [
                "live_scores",
                "thursday_performances", 
                "lineup_optimizer",
                "injury_updates"
            ],
            
            FantasyWeekPhase.PRE_GAMES: [
                "lineup_optimizer",
                "start_sit_recommendations",
                "injury_reports",
                "weather_updates",
                "last_minute_pickups"
            ],
            
            FantasyWeekPhase.GAMES_ACTIVE: [
                "live_scores",
                "real_time_matchup",
                "player_performances", 
                "injury_tracker",
                "scoreboard"
            ],
            
            FantasyWeekPhase.POST_GAMES: [
                "performance_analysis",
                "waiver_wire_targets",
                "league_recap",
                "player_trends",
                "next_week_preview"
            ],
            
            FantasyWeekPhase.WAIVERS_PROCESSING: [
                "waiver_results",
                "league_activity",
                "backup_targets"
            ]
        }
        
        return section_recommendations.get(phase, section_recommendations[FantasyWeekPhase.PLANNING])