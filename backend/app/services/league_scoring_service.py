"""
League-specific scoring service for calculating and storing fantasy points
"""
from typing import Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging

from app.models.sleeper import PlayerStats
from app.models.fantasy_points import FantasyPointCalculation
from app.models.leagues import League
from app.utils.scoring import calculate_fantasy_points
from app.services.stat_mapping_service import StatMappingService, StatType

logger = logging.getLogger(__name__)


class LeagueScoringService:
    """Service for calculating league-specific fantasy points and storing calculations"""

    def __init__(self, db: Session):
        self.db = db
        self.stat_mapper = StatMappingService()

    def get_league_scoring_settings(self, league_id: str) -> Dict:
        """Get scoring settings for a specific league"""
        league = self.db.query(League).filter(League.league_id == league_id).first()
        if not league or not league.scoring_settings:
            logger.warning(f"No scoring settings found for league {league_id}, using defaults")
            return self._get_default_scoring_settings()

        return league.scoring_settings

    def calculate_and_store_fantasy_points(
        self,
        league_id: str,
        stat_id: int,
        player_stats: PlayerStats,
        force_recalculate: bool = False
    ) -> Optional[float]:
        """
        Calculate league-specific fantasy points for a player stat and store in fantasy_point_calculations

        Args:
            league_id: League ID for scoring settings
            stat_id: PlayerStats record ID
            player_stats: PlayerStats object
            force_recalculate: Whether to recalculate if already exists

        Returns:
            Calculated fantasy points or None if calculation failed
        """
        try:
            # Check if calculation already exists
            existing = self.db.query(FantasyPointCalculation).filter(
                and_(
                    FantasyPointCalculation.league_id == league_id,
                    FantasyPointCalculation.stat_id == stat_id
                )
            ).first()

            if existing and not force_recalculate:
                return float(existing.fantasy_points)

            # Get league scoring settings
            scoring_settings = self.get_league_scoring_settings(league_id)

            # Both actual stats and projections use the same PlayerStats database fields
            # so they both use ACTUAL_STATS mapping
            stat_type = StatType.ACTUAL_STATS

            # Normalize stats using mapping service
            normalized_stats = self.stat_mapper.normalize_stats(
                stats=player_stats,
                stat_type=stat_type
            )

            # Get player position for position-specific bonuses (like TE premium)
            player_position = player_stats.player.position if player_stats.player else None

            # Calculate fantasy points using scoring function
            fantasy_points_dict = calculate_fantasy_points(
                stats=normalized_stats,
                scoring_settings=scoring_settings,
                player_position=player_position
            )

            # Use PPR scoring as default (most common format)
            fantasy_points = fantasy_points_dict.get('ppr', 0.0)

            # Create scoring breakdown for transparency
            scoring_breakdown = self._create_scoring_breakdown(
                normalized_stats, scoring_settings, fantasy_points_dict
            )

            if existing:
                # Update existing calculation
                existing.fantasy_points = fantasy_points
                existing.scoring_breakdown = scoring_breakdown
                logger.debug(f"Updated fantasy points calculation for league {league_id}, stat {stat_id}: {fantasy_points}")
            else:
                # Create new calculation
                calculation = FantasyPointCalculation(
                    league_id=league_id,
                    stat_id=stat_id,
                    fantasy_points=fantasy_points,
                    scoring_breakdown=scoring_breakdown
                )
                self.db.add(calculation)
                logger.debug(f"Created fantasy points calculation for league {league_id}, stat {stat_id}: {fantasy_points}")

            self.db.commit()
            return fantasy_points

        except Exception as e:
            logger.error(f"Failed to calculate fantasy points for league {league_id}, stat {stat_id}: {e}")
            self.db.rollback()
            return None

    def get_stored_fantasy_points(self, league_id: str, stat_id: int) -> Optional[Dict]:
        """Get stored fantasy point calculation"""
        calculation = self.db.query(FantasyPointCalculation).filter(
            and_(
                FantasyPointCalculation.league_id == league_id,
                FantasyPointCalculation.stat_id == stat_id
            )
        ).first()

        if calculation:
            return {
                'fantasy_points': float(calculation.fantasy_points),
                'scoring_breakdown': calculation.scoring_breakdown,
                'calculated_at': calculation.created_at.isoformat()
            }
        return None

    def bulk_calculate_fantasy_points(
        self,
        league_id: str,
        week: int,
        season: str,
        stat_type: str = 'actual'
    ) -> Dict[str, float]:
        """
        Calculate fantasy points for all players in a specific week for a league

        Args:
            league_id: League ID
            week: NFL week
            season: NFL season
            stat_type: 'actual' or 'projection'

        Returns:
            Dictionary mapping player_id -> fantasy_points
        """
        try:
            # Get all stats for the week
            stats_query = self.db.query(PlayerStats).filter(
                and_(
                    PlayerStats.week == week,
                    PlayerStats.season == season,
                    PlayerStats.stat_type == stat_type
                )
            ).all()

            results = {}
            for stat in stats_query:
                fantasy_points = self.calculate_and_store_fantasy_points(
                    league_id=league_id,
                    stat_id=stat.stat_id,
                    player_stats=stat
                )
                if fantasy_points is not None:
                    results[stat.player_id] = fantasy_points

            logger.info(f"Bulk calculated fantasy points for {len(results)} players in league {league_id}, week {week}")
            return results

        except Exception as e:
            logger.error(f"Failed bulk fantasy points calculation for league {league_id}, week {week}: {e}")
            return {}

    def _create_scoring_breakdown(
        self,
        normalized_stats: Dict,
        scoring_settings: Dict,
        fantasy_points_dict: Dict
    ) -> Dict:
        """Create detailed scoring breakdown for transparency"""
        breakdown = {
            'total_points': fantasy_points_dict.get('ppr', 0.0),
            'scoring_formats': {
                'ppr': fantasy_points_dict.get('ppr', 0.0),
                'standard': fantasy_points_dict.get('standard', 0.0),
                'half_ppr': fantasy_points_dict.get('half_ppr', 0.0)
            },
            'category_breakdown': {}
        }

        # Calculate points per category
        categories = {
            'passing': ['pass_yds', 'pass_tds', 'pass_ints', 'pass_sack', 'pass_2pt'],
            'rushing': ['rush_yds', 'rush_tds', 'rush_2pt'],
            'receiving': ['rec_yds', 'rec_tds', 'rec', 'rec_2pt'],
            'kicking': ['fgm', 'xpm', 'fgm_40_49', 'fgm_50_59', 'fgm_60p'],
            'defense': ['def_sack', 'def_int', 'def_td', 'def_safety'],
            'fumbles': ['fum_lost'],
            'tackles': ['tkl', 'tkl_solo', 'tkl_ast']  # Offensive player tackles
        }

        for category, stat_fields in categories.items():
            category_points = 0.0
            for stat_field in stat_fields:
                stat_value = normalized_stats.get(stat_field, 0)
                scoring_value = scoring_settings.get(self._map_stat_to_scoring_key(stat_field), 0)
                points = stat_value * scoring_value
                category_points += points

            if category_points != 0:
                breakdown['category_breakdown'][category] = round(category_points, 2)

        return breakdown

    def _map_stat_to_scoring_key(self, stat_field: str) -> str:
        """Map normalized stat field to scoring settings key"""
        # This mapping should match what's used in the scoring calculation
        mapping = {
            'pass_yds': 'pass_yd',
            'pass_tds': 'pass_td',
            'pass_ints': 'pass_int',
            'pass_sack': 'pass_sack',
            'rush_yds': 'rush_yd',
            'rush_tds': 'rush_td',
            'rec_yds': 'rec_yd',
            'rec_tds': 'rec_td',
            'rec': 'rec',
            'fum_lost': 'fum_lost',
            'fgm': 'fgm',
            'xpm': 'xpm',
            'def_sack': 'sack',
            'def_int': 'int',
            'def_td': 'def_td',
            'tkl': 'tkl',
            'tkl_solo': 'tkl_solo',
            'tkl_ast': 'tkl_ast',
            # Add more mappings as needed
        }
        return mapping.get(stat_field, stat_field)

    def _get_default_scoring_settings(self) -> Dict:
        """Get default scoring settings (similar to StatsService)"""
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

            # Receiving
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