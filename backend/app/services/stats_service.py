"""
Enhanced stats service for syncing player statistics and projections
"""
from typing import Dict, List, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging

from app.config import settings
from app.integrations.sleeper_api import SleeperAPIClient
from app.models.sleeper import PlayerStats
from app.models.players import Player
from app.models.sources import Source
from app.services.stat_mapping_service import StatMappingService, StatType
from app.services.player_mapping_service import PlayerMappingService
from app.utils.scoring import calculate_fantasy_points

logger = logging.getLogger(__name__)


class StatsService:
    """Enhanced service for syncing all player statistics and projections"""

    def __init__(self, db: Session):
        self.db = db
        self.client = SleeperAPIClient()
        self.stat_mapper = StatMappingService()
        self.player_mapper = PlayerMappingService(db)

        # Get or create Sleeper source
        self.sleeper_source = self._get_or_create_sleeper_source()

    def _get_or_create_sleeper_source(self) -> Source:
        """Get or create the Sleeper source record"""
        source = self.db.query(Source).filter(Source.name == "Sleeper").first()
        if not source:
            source = Source(
                name="Sleeper",
                source_type="league_data",
                data_method="api",
                base_weight=1.00,
                current_reliability_score=0.95,
                specialty="NFL Stats",
                update_frequency="daily",
                api_base_url="https://api.sleeper.app",
                is_active=True
            )
            self.db.add(source)
            self.db.commit()
            logger.info("Created Sleeper source record")
        return source

    async def sync_player_stats(self, week: int, season: str = None) -> int:
        """
        Sync player stats for a specific week with improved field mapping

        Args:
            week: NFL week number
            season: NFL season (defaults to current season)

        Returns:
            Number of player stats synced
        """
        season = season or settings.default_season

        try:
            logger.info(f"Syncing player stats for Week {week}, {season} season...")

            # Get stats from Sleeper API
            stats_data = await self.client.get_player_stats(week, season)
            count = 0

            for sleeper_id, raw_stats in stats_data.items():
                if self._should_sync_player_stats(raw_stats):
                    success = await self._upsert_player_stats(
                        sleeper_id=sleeper_id,
                        week=week,
                        season=season,
                        raw_stats=raw_stats,
                        stat_type='actual'
                    )
                    if success:
                        count += 1

            self.db.commit()
            logger.info(f"Successfully synced {count} player stats for week {week}")
            return count

        except Exception as e:
            logger.error(f"Failed to sync player stats: {e}")
            self.db.rollback()
            return 0

    async def sync_player_projections(self, week: int, season: str = None) -> int:
        """
        Sync player projections for a specific week with improved field mapping

        Args:
            week: NFL week number
            season: NFL season (defaults to current season)

        Returns:
            Number of player projections synced
        """
        season = season or settings.default_season

        try:
            logger.info(f"Syncing player projections for Week {week}, {season} season...")

            # Get projections from Sleeper API
            projections_data = await self.client.get_player_projections(week, season)
            count = 0

            for sleeper_id, raw_projections in projections_data.items():
                if self._should_sync_player_projections(raw_projections):
                    success = await self._upsert_player_stats(
                        sleeper_id=sleeper_id,
                        week=week,
                        season=season,
                        raw_stats=raw_projections,
                        stat_type='projection'
                    )
                    if success:
                        count += 1

            self.db.commit()
            logger.info(f"Successfully synced {count} player projections for week {week}")
            return count

        except Exception as e:
            logger.error(f"Failed to sync player projections: {e}")
            self.db.rollback()
            return 0

    async def _upsert_player_stats(
        self,
        sleeper_id: str,
        week: int,
        season: str,
        raw_stats: Dict,
        stat_type: str
    ) -> bool:
        """
        Insert or update player stats with proper field mapping and fantasy points calculation

        Args:
            sleeper_id: Sleeper player ID
            week: NFL week
            season: NFL season
            raw_stats: Raw stats from Sleeper API
            stat_type: 'actual' or 'projection'

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if player exists
            player = self.db.query(Player).filter(Player.player_id == sleeper_id).first()
            if not player:
                logger.warning(f"Player {sleeper_id} not found in database, skipping stats sync")
                return False

            # Check for existing record
            existing = self.db.query(PlayerStats).filter(
                and_(
                    PlayerStats.player_id == sleeper_id,
                    PlayerStats.week == week,
                    PlayerStats.season == season,
                    PlayerStats.stat_type == stat_type,
                    PlayerStats.source_id == self.sleeper_source.source_id
                )
            ).first()

            # Normalize stats using the stat mapping service
            sleeper_stat_type = StatType.SLEEPER_STATS if stat_type == 'actual' else StatType.RAW_PROJECTIONS
            normalized_stats = self.stat_mapper.normalize_stats(
                stats=raw_stats,
                stat_type=sleeper_stat_type,
                position=player.position
            )

            # Calculate fantasy points using normalized stats
            # Use default scoring settings - points will be calculated on-demand with league context
            default_scoring = self._get_default_scoring_settings()
            fantasy_points = calculate_fantasy_points(
                stats=normalized_stats,
                scoring_settings=default_scoring,
                player_position=player.position
            )

            ppr_points = fantasy_points.get('ppr', 0.0)
            standard_points = fantasy_points.get('standard', 0.0)
            half_ppr_points = fantasy_points.get('half_ppr', 0.0)

            if existing:
                # Update existing record
                self._update_player_stats(existing, raw_stats, ppr_points, standard_points, half_ppr_points)
            else:
                # Create new record
                new_stats = self._create_player_stats(
                    player_id=sleeper_id,
                    week=week,
                    season=season,
                    stat_type=stat_type,
                    raw_stats=raw_stats,
                    ppr_points=ppr_points,
                    standard_points=standard_points,
                    half_ppr_points=half_ppr_points
                )
                self.db.add(new_stats)

            return True

        except Exception as e:
            logger.error(f"Failed to upsert stats for player {sleeper_id}: {e}")
            return False

    def _create_player_stats(
        self,
        player_id: str,
        week: int,
        season: str,
        stat_type: str,
        raw_stats: Dict,
        ppr_points: float,
        standard_points: float,
        half_ppr_points: float
    ) -> PlayerStats:
        """Create new PlayerStats record with proper field mapping"""
        return PlayerStats(
            player_id=player_id,
            week=week,
            season=season,
            stat_type=stat_type,
            source_id=self.sleeper_source.source_id,

            # Fantasy points
            fantasy_points_ppr=ppr_points,
            fantasy_points_standard=standard_points,
            fantasy_points_half_ppr=half_ppr_points,

            # Passing stats (note the field name mapping)
            pass_yds=raw_stats.get('pass_yd'),  # Sleeper uses 'pass_yd'
            pass_tds=raw_stats.get('pass_td'),
            pass_ints=raw_stats.get('pass_int'),
            pass_att=raw_stats.get('pass_att'),
            pass_cmp=raw_stats.get('pass_cmp'),

            # Rushing stats
            rush_yds=raw_stats.get('rush_yd'),  # Sleeper uses 'rush_yd'
            rush_tds=raw_stats.get('rush_td'),
            rush_att=raw_stats.get('rush_att'),

            # Receiving stats
            rec_yds=raw_stats.get('rec_yd'),   # Sleeper uses 'rec_yd'
            rec_tds=raw_stats.get('rec_td'),
            rec=raw_stats.get('rec'),
            rec_tgt=raw_stats.get('rec_tgt'),

            # 2-point conversions
            pass_2pt=raw_stats.get('pass_2pt'),
            rush_2pt=raw_stats.get('rush_2pt'),
            rec_2pt=raw_stats.get('rec_2pt'),
            def_2pt=raw_stats.get('def_2pt'),

            # Fumbles
            fum=raw_stats.get('fum'),
            fum_lost=raw_stats.get('fum_lost'),
            pass_sack=raw_stats.get('pass_sack'),
            ff=raw_stats.get('ff'),
            fum_rec_td=raw_stats.get('fum_rec_td'),

            # Position bonuses
            bonus_rec_te=raw_stats.get('bonus_rec_te'),

            # Kicking stats
            fgm=raw_stats.get('fgm'),
            fga=raw_stats.get('fga'),
            xpm=raw_stats.get('xpm'),
            xpa=raw_stats.get('xpa'),

            # Distance-based field goals
            fgm_0_19=raw_stats.get('fgm_0_19'),
            fgm_20_29=raw_stats.get('fgm_20_29'),
            fgm_30_39=raw_stats.get('fgm_30_39'),
            fgm_40_49=raw_stats.get('fgm_40_49'),
            fgm_50_59=raw_stats.get('fgm_50_59'),
            fgm_60p=raw_stats.get('fgm_60p'),

            # Field goal misses
            fgmiss_0_19=raw_stats.get('fgmiss_0_19'),
            fgmiss_20_29=raw_stats.get('fgmiss_20_29'),
            fgmiss_30_39=raw_stats.get('fgmiss_30_39'),
            fgmiss_40_49=raw_stats.get('fgmiss_40_49'),

            # Kicking yards and misses
            fgm_yds=raw_stats.get('fgm_yds'),
            xpmiss=raw_stats.get('xpmiss'),

            # Defensive stats
            def_sack=raw_stats.get('sack'),
            def_int=raw_stats.get('int'),
            def_fumble_rec=raw_stats.get('fum_rec'),
            def_td=raw_stats.get('def_td'),
            def_safety=raw_stats.get('safe'),
            def_block_kick=raw_stats.get('blk_kick'),
            def_4_and_stop=raw_stats.get('def_4_and_stop'),
            def_pass_def=raw_stats.get('def_pass_def'),
            def_tackle_solo=raw_stats.get('def_tackle_solo'),
            def_tackle_assist=raw_stats.get('def_tackle_assist'),
            def_qb_hit=raw_stats.get('def_qb_hit'),
            def_tfl=raw_stats.get('def_tfl'),

            # Team defense - points allowed tiers
            pts_allow_0=raw_stats.get('pts_allow_0'),
            pts_allow_1_6=raw_stats.get('pts_allow_1_6'),
            pts_allow_7_13=raw_stats.get('pts_allow_7_13'),
            pts_allow_14_20=raw_stats.get('pts_allow_14_20'),
            pts_allow_21_27=raw_stats.get('pts_allow_21_27'),
            pts_allow_28_34=raw_stats.get('pts_allow_28_34'),
            pts_allow_35p=raw_stats.get('pts_allow_35p'),

            # Yards allowed tiers
            yds_allow_0_100=raw_stats.get('yds_allow_0_100'),
            yds_allow_100_199=raw_stats.get('yds_allow_100_199'),
            yds_allow_200_299=raw_stats.get('yds_allow_200_299'),
            yds_allow_300_349=raw_stats.get('yds_allow_300_349'),
            yds_allow_350_399=raw_stats.get('yds_allow_350_399'),
            yds_allow_400_449=raw_stats.get('yds_allow_400_449'),
            yds_allow_450_499=raw_stats.get('yds_allow_450_499'),
            yds_allow_500_549=raw_stats.get('yds_allow_500_549'),
            yds_allow_550p=raw_stats.get('yds_allow_550p'),

            # Continuous defense
            pts_allow=raw_stats.get('pts_allow'),
            yds_allow=raw_stats.get('yds_allow'),

            # Special teams
            st_td=raw_stats.get('st_td'),
            kr_yd=raw_stats.get('kr_yd'),
            pr_yd=raw_stats.get('pr_yd'),
            st_fum_rec=raw_stats.get('st_fum_rec'),
            st_ff=raw_stats.get('st_ff'),

            # IDP stats
            idp_tkl=raw_stats.get('idp_tkl'),

            # Offensive player tackle stats
            tkl=raw_stats.get('tkl'),
            tkl_solo=raw_stats.get('tkl_solo'),
            tkl_ast=raw_stats.get('tkl_ast'),

            # Store raw stats for debugging
            raw_stats=raw_stats,
        )

    def _update_player_stats(
        self,
        existing: PlayerStats,
        raw_stats: Dict,
        ppr_points: float,
        standard_points: float,
        half_ppr_points: float
    ):
        """Update existing PlayerStats record with proper field mapping"""
        # Fantasy points
        existing.fantasy_points_ppr = ppr_points
        existing.fantasy_points_standard = standard_points
        existing.fantasy_points_half_ppr = half_ppr_points

        # Passing stats (note the field name mapping)
        existing.pass_yds = raw_stats.get('pass_yd')  # Sleeper uses 'pass_yd'
        existing.pass_tds = raw_stats.get('pass_td')
        existing.pass_ints = raw_stats.get('pass_int')
        existing.pass_att = raw_stats.get('pass_att')
        existing.pass_cmp = raw_stats.get('pass_cmp')

        # Rushing stats
        existing.rush_yds = raw_stats.get('rush_yd')  # Sleeper uses 'rush_yd'
        existing.rush_tds = raw_stats.get('rush_td')
        existing.rush_att = raw_stats.get('rush_att')

        # Receiving stats
        existing.rec_yds = raw_stats.get('rec_yd')   # Sleeper uses 'rec_yd'
        existing.rec_tds = raw_stats.get('rec_td')
        existing.rec = raw_stats.get('rec')
        existing.rec_tgt = raw_stats.get('rec_tgt')

        # Update all other fields similarly...
        # (continuing with same pattern as create method)
        existing.pass_2pt = raw_stats.get('pass_2pt')
        existing.rush_2pt = raw_stats.get('rush_2pt')
        existing.rec_2pt = raw_stats.get('rec_2pt')
        existing.def_2pt = raw_stats.get('def_2pt')
        existing.fum = raw_stats.get('fum')
        existing.fum_lost = raw_stats.get('fum_lost')
        existing.pass_sack = raw_stats.get('pass_sack')
        existing.ff = raw_stats.get('ff')
        existing.fum_rec_td = raw_stats.get('fum_rec_td')
        existing.bonus_rec_te = raw_stats.get('bonus_rec_te')
        existing.fgm = raw_stats.get('fgm')
        existing.fga = raw_stats.get('fga')
        existing.xpm = raw_stats.get('xpm')
        existing.xpa = raw_stats.get('xpa')
        existing.fgm_0_19 = raw_stats.get('fgm_0_19')
        existing.fgm_20_29 = raw_stats.get('fgm_20_29')
        existing.fgm_30_39 = raw_stats.get('fgm_30_39')
        existing.fgm_40_49 = raw_stats.get('fgm_40_49')
        existing.fgm_50_59 = raw_stats.get('fgm_50_59')
        existing.fgm_60p = raw_stats.get('fgm_60p')
        existing.fgmiss_0_19 = raw_stats.get('fgmiss_0_19')
        existing.fgmiss_20_29 = raw_stats.get('fgmiss_20_29')
        existing.fgmiss_30_39 = raw_stats.get('fgmiss_30_39')
        existing.fgmiss_40_49 = raw_stats.get('fgmiss_40_49')
        existing.fgm_yds = raw_stats.get('fgm_yds')
        existing.xpmiss = raw_stats.get('xpmiss')
        existing.def_sack = raw_stats.get('sack')
        existing.def_int = raw_stats.get('int')
        existing.def_fumble_rec = raw_stats.get('fum_rec')
        existing.def_td = raw_stats.get('def_td')
        existing.def_safety = raw_stats.get('safe')
        existing.def_block_kick = raw_stats.get('blk_kick')
        existing.def_4_and_stop = raw_stats.get('def_4_and_stop')
        existing.def_pass_def = raw_stats.get('def_pass_def')
        existing.def_tackle_solo = raw_stats.get('def_tackle_solo')
        existing.def_tackle_assist = raw_stats.get('def_tackle_assist')
        existing.def_qb_hit = raw_stats.get('def_qb_hit')
        existing.def_tfl = raw_stats.get('def_tfl')
        existing.pts_allow_0 = raw_stats.get('pts_allow_0')
        existing.pts_allow_1_6 = raw_stats.get('pts_allow_1_6')
        existing.pts_allow_7_13 = raw_stats.get('pts_allow_7_13')
        existing.pts_allow_14_20 = raw_stats.get('pts_allow_14_20')
        existing.pts_allow_21_27 = raw_stats.get('pts_allow_21_27')
        existing.pts_allow_28_34 = raw_stats.get('pts_allow_28_34')
        existing.pts_allow_35p = raw_stats.get('pts_allow_35p')
        existing.yds_allow_0_100 = raw_stats.get('yds_allow_0_100')
        existing.yds_allow_100_199 = raw_stats.get('yds_allow_100_199')
        existing.yds_allow_200_299 = raw_stats.get('yds_allow_200_299')
        existing.yds_allow_300_349 = raw_stats.get('yds_allow_300_349')
        existing.yds_allow_350_399 = raw_stats.get('yds_allow_350_399')
        existing.yds_allow_400_449 = raw_stats.get('yds_allow_400_449')
        existing.yds_allow_450_499 = raw_stats.get('yds_allow_450_499')
        existing.yds_allow_500_549 = raw_stats.get('yds_allow_500_549')
        existing.yds_allow_550p = raw_stats.get('yds_allow_550p')
        existing.pts_allow = raw_stats.get('pts_allow')
        existing.yds_allow = raw_stats.get('yds_allow')
        existing.st_td = raw_stats.get('st_td')
        existing.kr_yd = raw_stats.get('kr_yd')
        existing.pr_yd = raw_stats.get('pr_yd')
        existing.st_fum_rec = raw_stats.get('st_fum_rec')
        existing.st_ff = raw_stats.get('st_ff')
        existing.idp_tkl = raw_stats.get('idp_tkl')
        existing.tkl = raw_stats.get('tkl')
        existing.tkl_solo = raw_stats.get('tkl_solo')
        existing.tkl_ast = raw_stats.get('tkl_ast')
        existing.raw_stats = raw_stats

    def _should_sync_player_stats(self, stats: Dict) -> bool:
        """Determine if player stats should be synced"""
        if not stats:
            return False

        # Check for meaningful stats (not all zeros)
        meaningful_stats = [
            'pass_yd', 'pass_td', 'rush_yd', 'rush_td', 'rec_yd', 'rec_td', 'rec',
            'fgm', 'xpm', 'def_sack', 'def_int', 'def_td', 'def_safety', 'def_fumble_rec',
            'pts_allow_0', 'pts_allow_1_6', 'pts_allow_7_13', 'pts_allow_14_20',
            'pts_allow_21_27', 'pts_allow_28_34', 'pts_allow_35p'
        ]

        return any(stats.get(stat, 0) > 0 for stat in meaningful_stats)

    def _should_sync_player_projections(self, projections: Dict) -> bool:
        """Determine if player projections should be synced"""
        if not projections:
            return False

        # Similar logic but for projections (can be non-zero floats)
        # Use Sleeper API field names, not our database field names
        meaningful_projections = [
            'pass_yd', 'pass_td', 'rush_yd', 'rush_td', 'rec_yd', 'rec_td', 'rec',
            'fgm', 'xpm', 'sack', 'int', 'def_td', 'safe', 'fum_rec',
            'def_4_and_stop', 'blk_kick'
        ]

        return any(float(projections.get(proj, 0)) > 0 for proj in meaningful_projections)

    def _get_default_scoring_settings(self) -> Dict:
        """Get default scoring settings for fantasy point calculation"""
        return {
            # Passing
            'pass_yd': 0.04,       # 1 point per 25 yards
            'pass_td': 4.0,        # 4 points per TD
            'pass_int': -2.0,      # -2 points per INT
            'pass_sack': -0.25,    # -0.25 points per sack taken
            'pass_2pt': 2.0,       # 2 points per 2PT conversion

            # Rushing
            'rush_yd': 0.1,        # 1 point per 10 yards
            'rush_td': 6.0,        # 6 points per TD
            'rush_2pt': 2.0,       # 2 points per 2PT conversion

            # Receiving (will be adjusted for PPR/Half-PPR/Standard)
            'rec_yd': 0.1,         # 1 point per 10 yards
            'rec_td': 6.0,         # 6 points per TD
            'rec': 1.0,            # 1 point per reception (PPR)
            'rec_2pt': 2.0,        # 2 points per 2PT conversion

            # Fumbles
            'fum_lost': -2.0,      # -2 points per fumble lost

            # Kicker
            'fgm': 3.0,            # 3 points per FG made
            'fga': 0.0,            # No penalty for FG attempts
            'xpm': 1.0,            # 1 point per XP made
            'xpa': 0.0,            # No penalty for XP attempts
            'xpmiss': -1.0,        # -1 point per XP missed

            # Distance bonuses for FG
            'fgm_0_19': 0.0,       # No bonus for short FG
            'fgm_20_29': 0.0,      # No bonus
            'fgm_30_39': 0.0,      # No bonus
            'fgm_40_49': 1.0,      # +1 for 40-49 yard FG
            'fgm_50_59': 2.0,      # +2 for 50-59 yard FG
            'fgm_60p': 3.0,        # +3 for 60+ yard FG

            # Defense
            'sack': 1.0,           # 1 point per sack
            'int': 2.0,            # 2 points per INT
            'fum_rec': 2.0,        # 2 points per fumble recovery
            'def_td': 6.0,         # 6 points per defensive TD
            'safe': 2.0,           # 2 points per safety
            'blk_kick': 2.0,       # 2 points per blocked kick

            # Points allowed (team defense)
            'pts_allow_0': 10.0,      # 10 points for shutout
            'pts_allow_1_6': 7.0,     # 7 points for 1-6 allowed
            'pts_allow_7_13': 4.0,    # 4 points for 7-13 allowed
            'pts_allow_14_20': 1.0,   # 1 point for 14-20 allowed
            'pts_allow_21_27': 0.0,   # 0 points for 21-27 allowed
            'pts_allow_28_34': -1.0,  # -1 point for 28-34 allowed
            'pts_allow_35p': -4.0,    # -4 points for 35+ allowed

            # Offensive player defensive stats (unusual but some leagues have this)
            'tkl': 1.0,              # +1 point for tackle by offensive player
            'tkl_solo': 1.0,         # +1 point for solo tackle by offensive player
            'tkl_ast': 0.5,          # +0.5 points for tackle assist by offensive player
            'idp_tkl': 1.0,          # +1 point for IDP tackles
        }

    async def close(self):
        """Close the API client"""
        await self.client.close()