from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.config import settings
from app.integrations.sleeper_api import SleeperAPIClient
from app.models.sleeper import SleeperLeague, SleeperRoster, SleeperPlayer, SleeperMatchup, SleeperPlayerStats, SleeperPlayerProjections
from app.models.players import Player
from app.services.player_mapping_service import PlayerMappingService
import logging

logger = logging.getLogger(__name__)

class SleeperService:
    """Service for syncing Sleeper data to our database"""
    
    def __init__(self, db: Session):
        self.db = db
        self.client = SleeperAPIClient()
        self.player_mapper = PlayerMappingService(db)
    
    async def find_user_by_username(self, username: str) -> Optional[Dict]:
        """Find a Sleeper user by username"""
        try:
            user = await self.client.get_user_by_username(username)
            return user
        except Exception as e:
            logger.error(f"Failed to find user {username}: {e}")
            return None
    
    async def sync_user_leagues(self, user_id: str, season: str = settings.default_season) -> List[SleeperLeague]:
        """Sync all leagues for a user"""
        try:
            leagues_data = await self.client.get_user_leagues(user_id, season)
            synced_leagues = []
            
            for league_data in leagues_data:
                league = await self._sync_league(league_data, user_id)
                if league:
                    synced_leagues.append(league)
                    
            return synced_leagues
            
        except Exception as e:
            logger.error(f"Failed to sync leagues for user {user_id}: {e}")
            return []
    
    async def sync_league_full(self, league_id: str, user_id: str) -> Optional[SleeperLeague]:
        """Fully sync a league including rosters and recent matchups"""
        try:
            # Get league info
            league_info = await self.client.get_league_info(league_id)
            league = await self._sync_league(league_info, user_id)
            
            if not league:
                return None
            
            # Sync rosters
            await self.sync_league_rosters(league_id)
            
            # Sync recent matchups (current week)
            nfl_state = await self.client.get_nfl_state()
            current_week = nfl_state.get('week', 1)
            await self.sync_league_matchups(league_id, current_week)
            
            return league
            
        except Exception as e:
            logger.error(f"Failed to sync league {league_id}: {e}")
            return None
    
    async def sync_league_rosters(self, league_id: str) -> List[SleeperRoster]:
        """Sync all rosters for a league"""
        try:
            rosters_data = await self.client.get_league_rosters(league_id)
            synced_rosters = []
            
            for roster_data in rosters_data:
                roster = self._upsert_roster(roster_data, league_id)
                synced_rosters.append(roster)
            
            self.db.commit()
            return synced_rosters
            
        except Exception as e:
            logger.error(f"Failed to sync rosters for league {league_id}: {e}")
            self.db.rollback()
            return []
    
    async def sync_league_matchups(self, league_id: str, week: int) -> List[SleeperMatchup]:
        """Sync matchups for a specific week"""
        try:
            matchups_data = await self.client.get_league_matchups(league_id, week)
            synced_matchups = []
            
            for matchup_data in matchups_data:
                matchup = self._upsert_matchup(matchup_data, league_id, week)
                synced_matchups.append(matchup)
            
            self.db.commit()
            return synced_matchups
            
        except Exception as e:
            logger.error(f"Failed to sync matchups for league {league_id}, week {week}: {e}")
            self.db.rollback()
            return []
    
    async def sync_players(self) -> int:
        """Sync all NFL players from Sleeper"""
        try:
            players_data = await self.client.get_all_players()
            count = 0
            
            for sleeper_id, player_data in players_data.items():
                if self._should_sync_player(player_data):
                    self._upsert_sleeper_player(sleeper_id, player_data)
                    count += 1
            
            self.db.commit()
            logger.info(f"Synced {count} players from Sleeper")
            return count
            
        except Exception as e:
            logger.error(f"Failed to sync players: {e}")
            self.db.rollback()
            return 0
    
    async def _sync_league(self, league_data: Dict, user_id: str) -> Optional[SleeperLeague]:
        """Sync a single league"""
        try:
            existing = self.db.query(SleeperLeague).filter(
                SleeperLeague.league_id == league_data['league_id']
            ).first()
            
            if existing:
                # Update existing
                existing.league_name = league_data.get('name')
                existing.status = league_data.get('status')
                existing.settings = league_data.get('settings')
                existing.scoring_settings = league_data.get('scoring_settings')
                existing.roster_positions = league_data.get('roster_positions')
                existing.total_rosters = league_data.get('total_rosters')
                league = existing
            else:
                # Create new
                league = SleeperLeague(
                    league_id=league_data['league_id'],
                    user_id=user_id,
                    sleeper_user_id=user_id,
                    league_name=league_data.get('name'),
                    season=league_data.get('season'),
                    status=league_data.get('status'),
                    sport=league_data.get('sport', 'nfl'),
                    settings=league_data.get('settings'),
                    scoring_settings=league_data.get('scoring_settings'),
                    roster_positions=league_data.get('roster_positions'),
                    total_rosters=league_data.get('total_rosters'),
                    draft_id=league_data.get('draft_id'),
                    previous_league_id=league_data.get('previous_league_id')
                )
                self.db.add(league)
            
            self.db.commit()
            return league
            
        except Exception as e:
            logger.error(f"Failed to sync league {league_data.get('league_id')}: {e}")
            self.db.rollback()
            return None
    
    def _upsert_roster(self, roster_data: Dict, league_id: str) -> SleeperRoster:
        """Insert or update a roster"""
        existing = self.db.query(SleeperRoster).filter(
            SleeperRoster.roster_id == roster_data['roster_id'],
            SleeperRoster.league_id == league_id
        ).first()
        
        if existing:
            # Update existing
            existing.owner_id = roster_data.get('owner_id')
            existing.player_ids = roster_data.get('players', [])
            existing.starters = roster_data.get('starters', [])
            existing.reserve = roster_data.get('reserve', [])
            existing.taxi = roster_data.get('taxi', [])
            existing.settings = roster_data.get('settings', {})
            
            # Update record stats if available
            settings = roster_data.get('settings', {})
            existing.wins = settings.get('wins', 0)
            existing.losses = settings.get('losses', 0)
            existing.ties = settings.get('ties', 0)
            existing.fpts = settings.get('fpts', 0)
            existing.fpts_against = settings.get('fpts_against', 0)
            
            return existing
        else:
            # Create new
            settings = roster_data.get('settings', {})
            roster = SleeperRoster(
                roster_id=roster_data['roster_id'],
                league_id=league_id,
                owner_id=roster_data.get('owner_id'),
                player_ids=roster_data.get('players', []),
                starters=roster_data.get('starters', []),
                reserve=roster_data.get('reserve', []),
                taxi=roster_data.get('taxi', []),
                settings=settings,
                wins=settings.get('wins', 0),
                losses=settings.get('losses', 0),
                ties=settings.get('ties', 0),
                fpts=settings.get('fpts', 0),
                fpts_against=settings.get('fpts_against', 0)
            )
            self.db.add(roster)
            return roster
    
    def _upsert_matchup(self, matchup_data: Dict, league_id: str, week: int) -> SleeperMatchup:
        """Insert or update a matchup"""
        existing = self.db.query(SleeperMatchup).filter(
            SleeperMatchup.league_id == league_id,
            SleeperMatchup.week == week,
            SleeperMatchup.roster_id == matchup_data['roster_id']
        ).first()
        
        if existing:
            # Update existing
            existing.matchup_id_sleeper = matchup_data.get('matchup_id')
            existing.points = matchup_data.get('points')
            existing.points_for = matchup_data.get('points')  # Same as points
            existing.starters = matchup_data.get('starters', [])
            existing.starters_points = matchup_data.get('starters_points', [])
            existing.players_points = matchup_data.get('players_points', {})
            existing.custom_points = matchup_data.get('custom_points')
            return existing
        else:
            # Create new
            matchup = SleeperMatchup(
                league_id=league_id,
                week=week,
                roster_id=matchup_data['roster_id'],
                matchup_id_sleeper=matchup_data.get('matchup_id'),
                points=matchup_data.get('points'),
                points_for=matchup_data.get('points'),
                starters=matchup_data.get('starters', []),
                starters_points=matchup_data.get('starters_points', []),
                players_points=matchup_data.get('players_points', {}),
                custom_points=matchup_data.get('custom_points')
            )
            self.db.add(matchup)
            return matchup

    def _upsert_sleeper_player(self, sleeper_id: str, player_data: Dict):
        """Insert or update a Sleeper player"""
        
        # Map Sleeper statuses to our enum values
        status_mapping = {
            'Active': 'Active',
            'Inactive': 'Inactive', 
            'Injured Reserve': 'Injured Reserve',
            'Reserve/PUP': 'Reserve/PUP',
            'Physically Unable to Perform': 'Reserve/PUP',  # Map to existing enum value
            'Non Football Injury': 'Inactive',  # Map to inactive
            'Suspended': 'Inactive',  # Map to inactive
            'Exempt': 'Inactive',  # Map to inactive
            'COVID-19': 'Inactive',  # Map to inactive
            'Reserve/COVID-19': 'Inactive',  # Map to inactive
        }
        
        raw_status = player_data.get('status', 'Active')
        mapped_status = status_mapping.get(raw_status, 'Active')  # Default to Active if unknown
        
        existing = self.db.query(SleeperPlayer).filter(
            SleeperPlayer.sleeper_player_id == sleeper_id
        ).first()
        
        if existing:
            # Update existing
            existing.full_name = player_data.get('full_name')
            existing.first_name = player_data.get('first_name')
            existing.last_name = player_data.get('last_name')
            existing.position = player_data.get('position')
            existing.team = player_data.get('team')
            existing.age = player_data.get('age')
            existing.height = player_data.get('height')
            existing.weight = player_data.get('weight')
            existing.college = player_data.get('college')
            existing.years_exp = player_data.get('years_exp')
            existing.status = mapped_status  # Use mapped status
            existing.fantasy_positions = player_data.get('fantasy_positions', [])
            
            # Update external IDs
            existing.espn_id = player_data.get('espn_id')
            existing.rotowire_id = player_data.get('rotowire_id')
            existing.fantasy_data_id = player_data.get('fantasy_data_id')
            existing.yahoo_id = player_data.get('yahoo_id')
            existing.stats_id = player_data.get('stats_id')
        else:
            # Create new
            sleeper_player = SleeperPlayer(
                sleeper_player_id=sleeper_id,
                full_name=player_data.get('full_name'),
                first_name=player_data.get('first_name'),
                last_name=player_data.get('last_name'),
                position=player_data.get('position'),
                team=player_data.get('team'),
                age=player_data.get('age'),
                height=player_data.get('height'),
                weight=player_data.get('weight'),
                college=player_data.get('college'),
                years_exp=player_data.get('years_exp'),
                status=mapped_status,  # Use mapped status
                fantasy_positions=player_data.get('fantasy_positions', []),
                
                # External IDs
                espn_id=player_data.get('espn_id'),
                rotowire_id=player_data.get('rotowire_id'),
                fantasy_data_id=player_data.get('fantasy_data_id'),
                yahoo_id=player_data.get('yahoo_id'),
                stats_id=player_data.get('stats_id')
            )
            self.db.add(sleeper_player)
    
    def _should_sync_player(self, player_data: Dict) -> bool:
        """Determine if we should sync this player"""
        # Only sync active NFL players with positions
        return (
            player_data.get('sport') == 'nfl' and
            player_data.get('position') is not None and
            player_data.get('status') != 'Inactive'
        )
    
    async def close(self):
        """Close the API client"""
        await self.client.close()

    async def sync_player_stats(self, week: int, season: str = settings.default_season) -> int:
        """Sync player stats for a specific week"""
        try:
            stats_data = await self.client.get_player_stats(week, season)
            count = 0
            
            # Sync individual player stats and team defenses
            # defense_count = 0
            for sleeper_id, stats in stats_data.items():
                # if sleeper_id.startswith('TEAM_'):
                #     # This is a team defense, strip the TEAM_ prefix
                #     team_id = sleeper_id.replace('TEAM_', '')
                #     await self._upsert_player_stats(team_id, week, season, stats)
                #     defense_count += 1
                # el
                if self._should_sync_player_stats(stats):
                    # Regular player stats
                    await self._upsert_player_stats(sleeper_id, week, season, stats)
                    count += 1
            
            self.db.commit()
            logger.info(f"Synced {count} player stats for week {week}")
            return count
            
        except Exception as e:
            logger.error(f"Failed to sync player stats: {e}")
            self.db.rollback()
            return 0

    async def sync_player_projections(self, week: int, season: str = settings.default_season) -> int:
        """Sync player projections for a specific week"""
        try:
            projections_data = await self.client.get_player_projections(week, season)
            count = 0
            
            for sleeper_id, projections in projections_data.items():
                if self._should_sync_player_projections(projections):
                    self._upsert_player_projections(sleeper_id, week, season, projections)
                    count += 1
            
            self.db.commit()
            logger.info(f"Synced {count} player projections for week {week}")
            return count
            
        except Exception as e:
            logger.error(f"Failed to sync player projections: {e}")
            self.db.rollback()
            return 0

    async def _upsert_player_stats(self, sleeper_id: str, week: int, season: str, stats: Dict):
        """Insert or update player stats"""        
        existing = self.db.query(SleeperPlayerStats).filter(
            SleeperPlayerStats.sleeper_player_id == sleeper_id,
            SleeperPlayerStats.week == week,
            SleeperPlayerStats.season == season
        ).first()
        
        if not existing:
            # Check if player exists in database
            player_exists = self.db.query(SleeperPlayer).filter(
                SleeperPlayer.sleeper_player_id == sleeper_id
            ).first()
            
            if not player_exists:
                logger.error(f"Player {sleeper_id} not found in database, skipping stats sync")
                return
            # If player exists but no stats, continue with the provided stats from the bulk response

        # Calculate fantasy points using standard scoring formats for storage
        ppr_points = self._calculate_fantasy_points(stats, scoring_type='ppr')
        standard_points = self._calculate_fantasy_points(stats, scoring_type='standard')
        half_ppr_points = self._calculate_fantasy_points(stats, scoring_type='half_ppr')
        
        if existing:
            # Update existing - using correct Sleeper API field names
            existing.fantasy_points_ppr = ppr_points
            existing.fantasy_points_standard = standard_points
            existing.fantasy_points_half_ppr = half_ppr_points
            existing.pass_yds = stats.get('pass_yd')  # Note: 'pass_yd' not 'pass_yds'
            existing.pass_tds = stats.get('pass_td')
            existing.pass_ints = stats.get('pass_int')
            existing.rush_yds = stats.get('rush_yd')  # Note: 'rush_yd' not 'rush_yds'
            existing.rush_tds = stats.get('rush_td')
            existing.rec_yds = stats.get('rec_yd')    # Note: 'rec_yd' not 'rec_yds'
            existing.rec_tds = stats.get('rec_td')
            existing.rec = stats.get('rec')
            # Defensive stats - using actual Sleeper field names
            existing.def_sack = stats.get('sack')
            existing.def_int = stats.get('int')  # 'int' not 'def_int'
            existing.def_fumble_rec = stats.get('fum_rec')  # Check if this exists
            existing.def_td = stats.get('def_td')
            existing.def_safety = stats.get('safe')  # Check if this exists
            existing.def_block_kick = stats.get('blk_kick')  # Check if this exists
            existing.def_pass_def = stats.get('def_pass_def')
            existing.def_tackle_solo = stats.get('tkl_solo')  # 'tkl_solo' not 'def_tackle_solo'
            existing.def_tackle_assist = stats.get('tkl_ast')  # 'tkl_ast' not 'def_tackle_assist'
            existing.def_qb_hit = stats.get('qb_hit')
            existing.def_tfl = stats.get('tkl_loss')  # 'tkl_loss' might be tackles for loss
            existing.raw_stats = stats
        else:
            # Create new - using correct Sleeper API field names
            player_stats = SleeperPlayerStats(
                sleeper_player_id=sleeper_id,
                week=week,
                season=season,
                fantasy_points_ppr=ppr_points,
                fantasy_points_standard=standard_points,
                fantasy_points_half_ppr=half_ppr_points,
                pass_yds=stats.get('pass_yd'),   # Note: 'pass_yd' not 'pass_yds'
                pass_tds=stats.get('pass_td'),
                pass_ints=stats.get('pass_int'),
                rush_yds=stats.get('rush_yd'),   # Note: 'rush_yd' not 'rush_yds'
                rush_tds=stats.get('rush_td'),
                rec_yds=stats.get('rec_yd'),     # Note: 'rec_yd' not 'rec_yds'
                rec_tds=stats.get('rec_td'),
                rec=stats.get('rec'),
                # Defensive stats - using actual Sleeper field names
                def_sack=stats.get('sack'),
                def_int=stats.get('int'),  # 'int' not 'def_int'
                def_fumble_rec=stats.get('fum_rec'),  # Check if this exists
                def_td=stats.get('def_td'),
                def_safety=stats.get('safe'),  # Check if this exists
                def_block_kick=stats.get('blk_kick'),  # Check if this exists
                def_pass_def=stats.get('def_pass_def'),
                def_tackle_solo=stats.get('tkl_solo'),  # 'tkl_solo' not 'def_tackle_solo'
                def_tackle_assist=stats.get('tkl_ast'),  # 'tkl_ast' not 'def_tackle_assist'
                def_qb_hit=stats.get('qb_hit'),
                def_tfl=stats.get('tkl_loss'),  # 'tkl_loss' might be tackles for loss
                raw_stats=stats
            )
            self.db.add(player_stats)

    def _calculate_fantasy_points(self, stats: Dict, scoring_type: str = 'ppr', scoring_settings: Optional[Dict] = None) -> float:
        """Calculate fantasy points based on stats and scoring settings"""
        points = 0.0
        
        # Use scoring settings if provided, otherwise fall back to defaults
        if scoring_settings:
            # Passing - using correct Sleeper field names
            points += (stats.get('pass_yd', 0) * scoring_settings.get('pass_yd', 0.04))
            points += (stats.get('pass_td', 0) * scoring_settings.get('pass_td', 4))
            points += (stats.get('pass_int', 0) * scoring_settings.get('pass_int', -2))
            points += (stats.get('pass_2pt', 0) * scoring_settings.get('pass_2pt', 2))
            
            # Rushing - using correct Sleeper field names
            points += (stats.get('rush_yd', 0) * scoring_settings.get('rush_yd', 0.1))
            points += (stats.get('rush_td', 0) * scoring_settings.get('rush_td', 6))
            points += (stats.get('rush_2pt', 0) * scoring_settings.get('rush_2pt', 2))
            
            # Receiving - using correct Sleeper field names
            points += (stats.get('rec_yd', 0) * scoring_settings.get('rec_yd', 0.1))
            points += (stats.get('rec_td', 0) * scoring_settings.get('rec_td', 6))
            points += (stats.get('rec', 0) * scoring_settings.get('rec', 0))  # PPR value from settings
            points += (stats.get('rec_2pt', 0) * scoring_settings.get('rec_2pt', 2))
            
            # Kicking
            points += (stats.get('fgm', 0) * scoring_settings.get('fgm', 3))
            points += (stats.get('xpm', 0) * scoring_settings.get('xpm', 1))
            points += (stats.get('fgmiss', 0) * scoring_settings.get('fgmiss', 0))
            
            # Defense/Special Teams - using actual Sleeper field names
            points += (stats.get('int', 0) * scoring_settings.get('def_int', 2))
            points += (stats.get('fum_rec', 0) * scoring_settings.get('def_fumble_rec', 2))
            points += (stats.get('sack', 0) * scoring_settings.get('def_sack', 1))
            points += (stats.get('def_td', 0) * scoring_settings.get('def_td', 6))
            points += (stats.get('safe', 0) * scoring_settings.get('def_safety', 2))
            points += (stats.get('blk_kick', 0) * scoring_settings.get('def_block_kick', 2))
            
        else:
            # Default scoring (fallback) - using correct Sleeper field names
            # Passing
            points += (stats.get('pass_yd', 0) * 0.04)  # 1 pt per 25 yards
            points += (stats.get('pass_td', 0) * 4)      # 4 pts per TD
            points += (stats.get('pass_int', 0) * -2)    # -2 pts per INT
            
            # Rushing
            points += (stats.get('rush_yd', 0) * 0.1)   # 1 pt per 10 yards
            points += (stats.get('rush_td', 0) * 6)      # 6 pts per TD
            
            # Receiving
            points += (stats.get('rec_yd', 0) * 0.1)    # 1 pt per 10 yards
            points += (stats.get('rec_td', 0) * 6)       # 6 pts per TD
            
            # PPR bonus
            if scoring_type in ['ppr', 'half_ppr']:
                multiplier = 1.0 if scoring_type == 'ppr' else 0.5
                points += (stats.get('rec', 0) * multiplier)
            
            # Kicking
            points += (stats.get('fgm', 0) * 3)          # 3 pts per FG
            points += (stats.get('xpm', 0) * 1)          # 1 pt per XP
        
        return round(points, 2)

    async def calculate_league_specific_points(self, league_id: str, raw_stats: Dict) -> float:
        """Calculate fantasy points using league-specific scoring settings"""
        try:
            league_info = await self.client.get_league_info(league_id)
            scoring_settings = league_info.get('scoring_settings', {})
            return self._calculate_fantasy_points(raw_stats, scoring_settings=scoring_settings)
        except Exception as e:
            logger.warning(f"Failed to get league scoring for {league_id}, using PPR default: {e}")
            return self._calculate_fantasy_points(raw_stats, scoring_type='ppr')

    def _should_sync_player_stats(self, stats: Dict) -> bool:
        """Determine if we should sync these player stats"""
        # Only sync if player has some statistical activity - using correct Sleeper field names
        return any(stats.get(key, 0) > 0 for key in [
            'pass_yd', 'rush_yd', 'rec_yd', 'pass_td', 'rush_td', 'rec_td', 'sack', 'int'
        ])