from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.config import settings
from app.integrations.sleeper_api import SleeperAPIClient
from app.models.sleeper import SleeperMatchup, PlayerStats, SleeperPlayerProjections
from app.models.leagues import League
from app.models.rosters import Roster
from app.models.players import Player
from app.services.player_mapping_service import PlayerMappingService
from app.utils.scoring import calculate_fantasy_points
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
    
    async def sync_user_leagues(self, user_id: str, season: str = settings.default_season) -> List[League]:
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
    
    async def sync_league_full(self, league_id: str, user_id: str) -> Optional[League]:
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
    
    async def sync_league_rosters(self, league_id: str) -> List[Roster]:
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
    
    async def _sync_league(self, league_data: Dict, user_id: str) -> Optional[League]:
        """Sync a single league"""
        try:
            existing = self.db.query(League).filter(
                League.league_id == league_data['league_id']
            ).first()
            
            if existing:
                # Update existing
                existing.league_name = league_data.get('name')
                existing.status = league_data.get('status')
                existing.scoring_settings = league_data.get('scoring_settings')
                existing.roster_positions = league_data.get('roster_positions')
                existing.total_teams = league_data.get('total_rosters')
                league = existing
            else:
                # Create new
                league = League(
                    league_id=league_data['league_id'],
                    platform='sleeper',
                    platform_league_id=league_data['league_id'],
                    user_id=user_id,
                    league_name=league_data.get('name'),
                    season=league_data.get('season'),
                    status=league_data.get('status'),
                    sport=league_data.get('sport', 'nfl'),
                    scoring_settings=league_data.get('scoring_settings'),
                    roster_positions=league_data.get('roster_positions'),
                    total_teams=league_data.get('total_rosters')
                )
                self.db.add(league)
            
            self.db.commit()
            return league
            
        except Exception as e:
            logger.error(f"Failed to sync league {league_data.get('league_id')}: {e}")
            self.db.rollback()
            return None
    
    def _upsert_roster(self, roster_data: Dict, league_id: str) -> Roster:
        """Insert or update a roster"""
        existing = self.db.query(Roster).filter(
            Roster.platform_roster_id == roster_data['roster_id'],
            Roster.league_id == league_id
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
            roster = Roster(
                platform_roster_id=roster_data['roster_id'],
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
        
        # Handle missing full_name - create from first_name + last_name if available
        full_name = player_data.get('full_name')
        first_name = player_data.get('first_name')
        last_name = player_data.get('last_name')
        
        if not full_name and first_name and last_name:
            full_name = f"{first_name} {last_name}"
        
        existing = self.db.query(Player).filter(
            Player.player_id == sleeper_id
        ).first()
        
        if existing:
            # Update existing
            existing.full_name = full_name
            existing.first_name = first_name
            existing.last_name = last_name
            existing.position = player_data.get('position')
            # Handle team code mapping (OAK -> LV)
            team = player_data.get('team')
            if team == 'OAK':
                team = 'LV'
            existing.team = team
            existing.age = player_data.get('age')
            existing.height = player_data.get('height')
            existing.weight = player_data.get('weight')
            existing.college = player_data.get('college')
            existing.years_exp = player_data.get('years_exp')
            existing.status = mapped_status  # Use mapped status
            existing.fantasy_positions = player_data.get('fantasy_positions', [])
            existing.sleeper_id = sleeper_id  # Set sleeper_id
            
            # Update external IDs
            existing.espn_id = player_data.get('espn_id')
            existing.rotowire_id = player_data.get('rotowire_id')
            existing.fantasy_data_id = player_data.get('fantasy_data_id')
            existing.yahoo_id = player_data.get('yahoo_id')
            existing.stats_id = player_data.get('stats_id')
        else:
            # Create new
            # Handle team code mapping (OAK -> LV)
            team = player_data.get('team')
            if team == 'OAK':
                team = 'LV'

            player = Player(
                player_id=sleeper_id,
                full_name=full_name,
                first_name=first_name,
                last_name=last_name,
                position=player_data.get('position'),
                team=team,
                age=player_data.get('age'),
                height=player_data.get('height'),
                weight=player_data.get('weight'),
                college=player_data.get('college'),
                years_exp=player_data.get('years_exp'),
                status=mapped_status,  # Use mapped status
                fantasy_positions=player_data.get('fantasy_positions', []),
                sleeper_id=sleeper_id,
                primary_data_source='sleeper',

                # External IDs
                espn_id=player_data.get('espn_id'),
                rotowire_id=player_data.get('rotowire_id'),
                fantasy_data_id=player_data.get('fantasy_data_id'),
                yahoo_id=player_data.get('yahoo_id'),
                stats_id=player_data.get('stats_id')
            )
            self.db.add(player)
    
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
            for sleeper_id, stats in stats_data.items():
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
        existing = self.db.query(PlayerStats).filter(
            PlayerStats.player_id == sleeper_id,
            PlayerStats.week == week,
            PlayerStats.season == season
        ).first()
        
        if not existing:
            # Check if player exists in database
            player_exists = self.db.query(Player).filter(
                Player.player_id == sleeper_id
            ).first()
            
            if not player_exists:
                logger.error(f"Player {sleeper_id} not found in database, skipping stats sync")
                return
            # If player exists but no stats, continue with the provided stats from the bulk response

        # Store raw stats only - fantasy points will be calculated on-demand with league context
        # This avoids the need for fallback scoring and ensures accuracy
        ppr_points = None  # Will calculate on-demand
        standard_points = None  # Will calculate on-demand
        half_ppr_points = None  # Will calculate on-demand
        
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
            # Kicking stats - Basic
            existing.fgm = stats.get('fgm')
            existing.fga = stats.get('fga')
            existing.xpm = stats.get('xpm')
            existing.xpa = stats.get('xpa')

            # Distance-based kicking
            existing.fgm_0_19 = stats.get('fgm_0_19')
            existing.fgm_20_29 = stats.get('fgm_20_29')
            existing.fgm_30_39 = stats.get('fgm_30_39')
            existing.fgm_40_49 = stats.get('fgm_40_49')
            existing.fgm_50_59 = stats.get('fgm_50_59')
            existing.fgm_60p = stats.get('fgm_60p')
            existing.fgmiss_0_19 = stats.get('fgmiss_0_19')
            existing.fgmiss_20_29 = stats.get('fgmiss_20_29')
            existing.fgmiss_30_39 = stats.get('fgmiss_30_39')
            existing.fgmiss_40_49 = stats.get('fgmiss_40_49')
            existing.fgm_yds = stats.get('fgm_yds')
            existing.xpmiss = stats.get('xpmiss')

            # 2-point conversions
            existing.pass_2pt = stats.get('pass_2pt')
            existing.rush_2pt = stats.get('rush_2pt')
            existing.rec_2pt = stats.get('rec_2pt')
            existing.def_2pt = stats.get('def_2pt')

            # Fumbles and penalties
            existing.fum = stats.get('fum')
            existing.fum_lost = stats.get('fum_lost')
            existing.pass_sack = stats.get('pass_sack')
            existing.ff = stats.get('ff')
            existing.fum_rec_td = stats.get('fum_rec_td')
            existing.bonus_rec_te = stats.get('bonus_rec_te')
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

            # Defense - Points allowed tiers
            existing.pts_allow_0 = stats.get('pts_allow_0')
            existing.pts_allow_1_6 = stats.get('pts_allow_1_6')
            existing.pts_allow_7_13 = stats.get('pts_allow_7_13')
            existing.pts_allow_14_20 = stats.get('pts_allow_14_20')
            existing.pts_allow_21_27 = stats.get('pts_allow_21_27')
            existing.pts_allow_28_34 = stats.get('pts_allow_28_34')
            existing.pts_allow_35p = stats.get('pts_allow_35p')
            existing.pts_allow = stats.get('pts_allow')

            # Defense - Yards allowed tiers
            existing.yds_allow_0_100 = stats.get('yds_allow_0_100')
            existing.yds_allow_100_199 = stats.get('yds_allow_100_199')
            existing.yds_allow_200_299 = stats.get('yds_allow_200_299')
            existing.yds_allow_300_349 = stats.get('yds_allow_300_349')
            existing.yds_allow_350_399 = stats.get('yds_allow_350_399')
            existing.yds_allow_400_449 = stats.get('yds_allow_400_449')
            existing.yds_allow_450_499 = stats.get('yds_allow_450_499')
            existing.yds_allow_500_549 = stats.get('yds_allow_500_549')
            existing.yds_allow_550p = stats.get('yds_allow_550p')
            existing.yds_allow = stats.get('yds_allow')

            # Additional defensive stats
            existing.def_4_and_stop = stats.get('def_4_and_stop')
            existing.def_st_td = stats.get('def_st_td')
            existing.def_st_fum_rec = stats.get('def_st_fum_rec')
            existing.def_st_ff = stats.get('def_st_ff')
            existing.idp_tkl = stats.get('idp_tkl')

            # Special teams return stats
            existing.kr_yd = stats.get('kr_yd')
            existing.pr_yd = stats.get('pr_yd')
            existing.st_td = stats.get('st_td')
            existing.st_fum_rec = stats.get('st_fum_rec')
            existing.st_ff = stats.get('st_ff')

            existing.raw_stats = stats
        else:
            # Create new - using correct Sleeper API field names
            player_stats = PlayerStats(
                player_id=sleeper_id,
                week=week,
                season=season,
                stat_type='actual',  # These are actual stats from Sleeper
                source_id=8,  # Sleeper source ID
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
                # Kicking stats - Basic
                fgm=stats.get('fgm'),
                fga=stats.get('fga'),
                xpm=stats.get('xpm'),
                xpa=stats.get('xpa'),

                # Distance-based kicking
                fgm_0_19=stats.get('fgm_0_19'),
                fgm_20_29=stats.get('fgm_20_29'),
                fgm_30_39=stats.get('fgm_30_39'),
                fgm_40_49=stats.get('fgm_40_49'),
                fgm_50_59=stats.get('fgm_50_59'),
                fgm_60p=stats.get('fgm_60p'),
                fgmiss_0_19=stats.get('fgmiss_0_19'),
                fgmiss_20_29=stats.get('fgmiss_20_29'),
                fgmiss_30_39=stats.get('fgmiss_30_39'),
                fgmiss_40_49=stats.get('fgmiss_40_49'),
                fgm_yds=stats.get('fgm_yds'),
                xpmiss=stats.get('xpmiss'),

                # 2-point conversions
                pass_2pt=stats.get('pass_2pt'),
                rush_2pt=stats.get('rush_2pt'),
                rec_2pt=stats.get('rec_2pt'),
                def_2pt=stats.get('def_2pt'),

                # Fumbles and penalties
                fum=stats.get('fum'),
                fum_lost=stats.get('fum_lost'),
                pass_sack=stats.get('pass_sack'),
                ff=stats.get('ff'),
                fum_rec_td=stats.get('fum_rec_td'),
                bonus_rec_te=stats.get('bonus_rec_te'),
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

                # Defense - Points allowed tiers
                pts_allow_0=stats.get('pts_allow_0'),
                pts_allow_1_6=stats.get('pts_allow_1_6'),
                pts_allow_7_13=stats.get('pts_allow_7_13'),
                pts_allow_14_20=stats.get('pts_allow_14_20'),
                pts_allow_21_27=stats.get('pts_allow_21_27'),
                pts_allow_28_34=stats.get('pts_allow_28_34'),
                pts_allow_35p=stats.get('pts_allow_35p'),
                pts_allow=stats.get('pts_allow'),

                # Defense - Yards allowed tiers
                yds_allow_0_100=stats.get('yds_allow_0_100'),
                yds_allow_100_199=stats.get('yds_allow_100_199'),
                yds_allow_200_299=stats.get('yds_allow_200_299'),
                yds_allow_300_349=stats.get('yds_allow_300_349'),
                yds_allow_350_399=stats.get('yds_allow_350_399'),
                yds_allow_400_449=stats.get('yds_allow_400_449'),
                yds_allow_450_499=stats.get('yds_allow_450_499'),
                yds_allow_500_549=stats.get('yds_allow_500_549'),
                yds_allow_550p=stats.get('yds_allow_550p'),
                yds_allow=stats.get('yds_allow'),

                # Additional defensive stats
                def_4_and_stop=stats.get('def_4_and_stop'),
                def_st_td=stats.get('def_st_td'),
                def_st_fum_rec=stats.get('def_st_fum_rec'),
                def_st_ff=stats.get('def_st_ff'),
                idp_tkl=stats.get('idp_tkl'),

                # Special teams return stats
                kr_yd=stats.get('kr_yd'),
                pr_yd=stats.get('pr_yd'),
                st_td=stats.get('st_td'),
                st_fum_rec=stats.get('st_fum_rec'),
                st_ff=stats.get('st_ff'),

                raw_stats=stats
            )
            self.db.add(player_stats)

    # Removed duplicate _calculate_fantasy_points method - now using shared utility

    async def calculate_league_specific_points(self, league_id: str, raw_stats: Dict) -> float:
        """Calculate fantasy points using league-specific scoring settings"""
        try:
            league_info = await self.client.get_league_info(league_id)
            scoring_settings = league_info.get('scoring_settings', {})
            if not scoring_settings:
                raise ValueError(f"No scoring settings found for league {league_id}")

            # Use shared scoring utility - assume half_ppr for sleeper service
            points_dict = calculate_fantasy_points(raw_stats, scoring_settings)
            return points_dict['half_ppr']
        except Exception as e:
            logger.error(f"Failed to get league scoring for {league_id}: {e}")
            raise RuntimeError(f"Cannot calculate fantasy points without league scoring settings for league {league_id}") from e

    def _should_sync_player_stats(self, stats: Dict) -> bool:
        """Determine if we should sync these player stats"""
        # Only sync if player has some statistical activity - using correct Sleeper field names
        return any(stats.get(key, 0) > 0 for key in [
            # Basic offensive stats
            'pass_yd', 'rush_yd', 'rec_yd', 'pass_td', 'rush_td', 'rec_td',

            # Kicker stats
            'fgm', 'xpm', 'fga', 'xpa', 'fgm_0_19', 'fgm_20_29', 'fgm_30_39', 'fgm_40_49', 'fgm_50_59', 'fgm_60p',
            'fgmiss_0_19', 'fgmiss_20_29', 'fgmiss_30_39', 'fgmiss_40_49', 'xpmiss', 'fgm_yds',

            # Defense stats
            'sack', 'int', 'fum_rec', 'def_td', 'safe', 'blk_kick', 'def_4_and_stop', 'ff',

            # Team defense points/yards allowed
            'pts_allow_0', 'pts_allow_1_6', 'pts_allow_7_13', 'pts_allow_14_20', 'pts_allow_21_27', 'pts_allow_28_34', 'pts_allow_35p',
            'yds_allow_0_100', 'yds_allow_100_199', 'yds_allow_200_299', 'yds_allow_300_349', 'yds_allow_350_399',
            'yds_allow_400_449', 'yds_allow_450_499', 'yds_allow_500_549', 'yds_allow_550p',

            # Special teams
            'st_td', 'def_st_td', 'kr_yd', 'pr_yd', 'st_fum_rec', 'def_st_fum_rec', 'st_ff', 'def_st_ff',

            # 2-point conversions
            'pass_2pt', 'rush_2pt', 'rec_2pt', 'def_2pt',

            # Other penalties/bonuses
            'fum_lost', 'pass_sack', 'bonus_rec_te', 'fum_rec_td', 'idp_tkl'
        ])

    def _should_sync_player_projections(self, projections: Dict) -> bool:
        """Determine if we should sync these player projections"""
        # Sync if player has any meaningful projections - using correct Sleeper field names
        return any(projections.get(key, 0) > 0 for key in [
            # Basic offensive projections - note: Sleeper uses 'pass_yd' not 'pass_yds'
            'pass_yd', 'rush_yd', 'rec_yd', 'pass_td', 'rush_td', 'rec_td',

            # Kicker projections
            'fgm', 'xpm', 'fga', 'xpa',

            # Defense projections
            'sack', 'int', 'fum_rec', 'def_td', 'safe',

            # Fantasy points projections
            'pts_ppr', 'pts_std', 'pts_half_ppr'
        ])

    def _upsert_player_projections(self, sleeper_id: str, week: int, season: str, projections: Dict):
        """Insert or update player projections"""
        from app.models.sleeper import SleeperPlayerProjections

        existing = self.db.query(SleeperPlayerProjections).filter(
            SleeperPlayerProjections.sleeper_player_id == sleeper_id,
            SleeperPlayerProjections.week == week,
            SleeperPlayerProjections.season == season
        ).first()

        if existing:
            # Update existing projections
            existing.projected_points_ppr = projections.get('projected_points_ppr', 0)
            existing.projected_points_standard = projections.get('projected_points_standard', 0)
            existing.projected_points_half_ppr = projections.get('projected_points_half_ppr', 0)
            # Use correct Sleeper projection field names
            existing.proj_pass_yds = projections.get('pass_yd', 0)  # Note: 'yd' not 'yds'
            existing.proj_pass_tds = projections.get('pass_td', 0)
            existing.proj_rush_yds = projections.get('rush_yd', 0)
            existing.proj_rush_tds = projections.get('rush_td', 0)
            existing.proj_rec_yds = projections.get('rec_yd', 0)
            existing.proj_rec_tds = projections.get('rec_td', 0)
            existing.proj_rec = projections.get('rec', 0)
            existing.raw_projections = projections  # Store raw data
        else:
            # Check if player exists
            player_exists = self.db.query(Player).filter(
                Player.player_id == sleeper_id
            ).first()

            if not player_exists:
                logger.error(f"Player {sleeper_id} not found in database, skipping projections sync")
                return

            # Create new projections
            player_projections = SleeperPlayerProjections(
                sleeper_player_id=sleeper_id,
                week=week,
                season=season,
                projected_points_ppr=projections.get('projected_points_ppr', 0),
                projected_points_standard=projections.get('projected_points_standard', 0),
                projected_points_half_ppr=projections.get('projected_points_half_ppr', 0),
                proj_pass_yds=projections.get('pass_yd', 0),
                proj_pass_tds=projections.get('pass_td', 0),
                proj_rush_yds=projections.get('rush_yd', 0),
                proj_rush_tds=projections.get('rush_td', 0),
                proj_rec_yds=projections.get('rec_yd', 0),
                proj_rec_tds=projections.get('rec_td', 0),
                proj_rec=projections.get('rec', 0),
                raw_projections=projections
            )
            self.db.add(player_projections)