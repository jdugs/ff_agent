"""
Unified stat mapping service to handle all fantasy football statistics consistently
"""
from typing import Dict, Any, Optional, Union
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class StatType(Enum):
    """Types of stat objects we handle"""
    ACTUAL_STATS = "actual_stats"  # From PlayerStats (database)
    CONSENSUS_PROJECTIONS = "consensus_projections"  # From consensus aggregation
    RAW_PROJECTIONS = "raw_projections"  # From raw Sleeper/FantasyPros data
    SLEEPER_STATS = "sleeper_stats"  # Direct from Sleeper API


class StatMappingService:
    """
    Centralized service for mapping all stat formats to a unified format
    that works with the scoring calculation system
    """

    def __init__(self):
        # Define the canonical stat field names (what scoring function expects)
        self.CANONICAL_FIELDS = {
            # Passing
            'pass_yds': 'Passing Yards',
            'pass_tds': 'Passing Touchdowns',
            'pass_ints': 'Passing Interceptions',
            'pass_att': 'Passing Attempts',
            'pass_cmp': 'Passing Completions',
            'pass_sack': 'Passing Sacks Taken',
            'pass_2pt': 'Passing 2-Point Conversions',

            # Rushing
            'rush_yds': 'Rushing Yards',
            'rush_tds': 'Rushing Touchdowns',
            'rush_att': 'Rushing Attempts',
            'rush_2pt': 'Rushing 2-Point Conversions',

            # Receiving
            'rec_yds': 'Receiving Yards',
            'rec_tds': 'Receiving Touchdowns',
            'rec': 'Receptions',
            'rec_tgt': 'Targets',
            'rec_2pt': 'Receiving 2-Point Conversions',

            # Fumbles
            'fum': 'Fumbles',
            'fum_lost': 'Fumbles Lost',
            'ff': 'Forced Fumbles',
            'fum_rec_td': 'Fumble Recovery TD',

            # Kicking
            'fgm': 'Field Goals Made',
            'fga': 'Field Goals Attempted',
            'xpm': 'Extra Points Made',
            'xpa': 'Extra Points Attempted',
            'xpmiss': 'Extra Points Missed',
            'fgm_yds': 'Field Goal Yards',

            # Distance-based FG
            'fgm_0_19': 'FG Made 0-19',
            'fgm_20_29': 'FG Made 20-29',
            'fgm_30_39': 'FG Made 30-39',
            'fgm_40_49': 'FG Made 40-49',
            'fgm_50_59': 'FG Made 50-59',
            'fgm_60p': 'FG Made 60+',

            # FG Misses
            'fgmiss_0_19': 'FG Miss 0-19',
            'fgmiss_20_29': 'FG Miss 20-29',
            'fgmiss_30_39': 'FG Miss 30-39',
            'fgmiss_40_49': 'FG Miss 40-49',

            # Defense
            'def_sack': 'Sacks',
            'def_int': 'Interceptions',
            'def_fumble_rec': 'Fumble Recoveries',
            'def_td': 'Defensive TDs',
            'def_safety': 'Safeties',
            'def_block_kick': 'Blocked Kicks',
            'def_4_and_stop': '4th Down Stops',

            # Points allowed tiers
            'pts_allow_0': 'Points Allowed 0',
            'pts_allow_1_6': 'Points Allowed 1-6',
            'pts_allow_7_13': 'Points Allowed 7-13',
            'pts_allow_14_20': 'Points Allowed 14-20',
            'pts_allow_21_27': 'Points Allowed 21-27',
            'pts_allow_28_34': 'Points Allowed 28-34',
            'pts_allow_35p': 'Points Allowed 35+',

            # Yards allowed tiers
            'yds_allow_0_100': 'Yards Allowed 0-100',
            'yds_allow_100_199': 'Yards Allowed 100-199',
            'yds_allow_200_299': 'Yards Allowed 200-299',
            'yds_allow_300_349': 'Yards Allowed 300-349',
            'yds_allow_350_399': 'Yards Allowed 350-399',
            'yds_allow_400_449': 'Yards Allowed 400-449',
            'yds_allow_450_499': 'Yards Allowed 450-499',
            'yds_allow_500_549': 'Yards Allowed 500-549',
            'yds_allow_550p': 'Yards Allowed 550+',

            # Continuous defense
            'pts_allow': 'Total Points Allowed',
            'yds_allow': 'Total Yards Allowed',

            # Special teams
            'st_td': 'Special Teams TD',
            'kr_yd': 'Kick Return Yards',
            'pr_yd': 'Punt Return Yards',
            'st_fum_rec': 'ST Fumble Recovery',
            'st_ff': 'ST Forced Fumble',

            # IDP
            'idp_tkl': 'Solo Tackles',
            'def_pass_def': 'Pass Deflections',
            'def_tackle_solo': 'Solo Tackles',
            'def_tackle_assist': 'Tackle Assists',
            'def_qb_hit': 'QB Hits',
            'def_tfl': 'Tackles for Loss',
        }

        # Define mappings from different stat formats to canonical format
        self.MAPPINGS = {
            StatType.ACTUAL_STATS: {
                # PlayerStats database fields -> canonical fields
                'pass_yds': 'pass_yds',
                'pass_tds': 'pass_tds',
                'pass_ints': 'pass_ints',
                'rush_yds': 'rush_yds',
                'rush_tds': 'rush_tds',
                'rec_yds': 'rec_yds',
                'rec_tds': 'rec_tds',
                'rec': 'rec',
                'fgm': 'fgm',
                'xpm': 'xpm',
                'fga': 'fga',
                'xpa': 'xpa',
                # Add more as needed - most should be 1:1 mapping
            },

            StatType.CONSENSUS_PROJECTIONS: {
                # Consensus projection fields -> canonical fields
                'passing_yards': 'pass_yds',
                'passing_tds': 'pass_tds',
                'passing_interceptions': 'pass_ints',
                'passing_attempts': 'pass_att',
                'passing_completions': 'pass_cmp',
                'rushing_yards': 'rush_yds',
                'rushing_tds': 'rush_tds',
                'rushing_attempts': 'rush_att',
                'receiving_yards': 'rec_yds',
                'receiving_tds': 'rec_tds',
                'receptions': 'rec',
                'targets': 'rec_tgt',
                'fumbles_lost': 'fum_lost',

                # Kicker stats
                'field_goals_made': 'fgm',
                'field_goals_attempted': 'fga',
                'extra_points_made': 'xpm',
                'extra_points_attempted': 'xpa',
                'field_goal_yards': 'fgm_yds',

                # Distance-based field goals
                'fg_0_19': 'fgm_0_19',
                'fg_20_29': 'fgm_20_29',
                'fg_30_39': 'fgm_30_39',
                'fg_40_49': 'fgm_40_49',
                'fg_50_plus': 'fgm_50_59',  # Map 50+ to 50-59
                'fg_60_plus': 'fgm_60p',

                # Defense stats
                'sacks': 'def_sack',
                'interceptions': 'def_int',
                'fumble_recoveries': 'def_fumble_rec',
                'defensive_tds': 'def_td',
                'safeties': 'def_safety',
                'blocked_kicks': 'def_block_kick',
                'fourth_down_stops': 'def_4_and_stop',

                # Points allowed tiers
                'pts_allow_0': 'pts_allow_0',
                'pts_allow_1_6': 'pts_allow_1_6',
                'pts_allow_7_13': 'pts_allow_7_13',
                'pts_allow_14_20': 'pts_allow_14_20',
                'pts_allow_21_27': 'pts_allow_21_27',
                'pts_allow_28_34': 'pts_allow_28_34',
                'pts_allow_35_plus': 'pts_allow_35p',

                # Yards allowed tiers
                'yds_allow_0_100': 'yds_allow_0_100',
                'yds_allow_100_199': 'yds_allow_100_199',
                'yds_allow_200_299': 'yds_allow_200_299',
                'yds_allow_300_349': 'yds_allow_300_349',
                'yds_allow_350_399': 'yds_allow_350_399',
                'yds_allow_400_plus': 'yds_allow_400_449',

                # Continuous defense
                'total_points_allowed': 'pts_allow',
                'total_yards_allowed': 'yds_allow',
            },

            StatType.RAW_PROJECTIONS: {
                # Raw Sleeper/FantasyPros projection fields -> canonical fields
                'pass_yd': 'pass_yds',
                'pass_td': 'pass_tds',
                'pass_int': 'pass_ints',
                'rush_yd': 'rush_yds',
                'rush_td': 'rush_tds',
                'rec_yd': 'rec_yds',
                'rec_td': 'rec_tds',
                'rec': 'rec',
                'fgm': 'fgm',
                'xpm': 'xpm',
                # Add all raw field mappings
            },

            StatType.SLEEPER_STATS: {
                # Direct Sleeper API stat fields -> canonical fields
                # These might be the same as RAW_PROJECTIONS or ACTUAL_STATS
                'pass_yd': 'pass_yds',
                'pass_td': 'pass_tds',
                # Add as needed
            }
        }

    def normalize_stats(
        self,
        stats: Union[Dict, Any],
        stat_type: StatType,
        position: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Convert any stat format to the canonical format for scoring calculation

        Args:
            stats: Stats object (dict or database object)
            stat_type: Type of stats (actual, projections, etc.)
            position: Player position for position-specific logic

        Returns:
            Dict with canonical field names and float values
        """
        if not stats:
            return {}

        mapping = self.MAPPINGS.get(stat_type, {})
        normalized = {}

        for source_field, canonical_field in mapping.items():
            # Get value from stats (handle both dict and object)
            if hasattr(stats, source_field):
                value = getattr(stats, source_field, 0)
            else:
                value = stats.get(source_field, 0) if isinstance(stats, dict) else 0

            # Convert to float safely
            try:
                normalized[canonical_field] = float(value) if value is not None else 0.0
            except (ValueError, TypeError):
                normalized[canonical_field] = 0.0

        logger.debug(f"Normalized {stat_type.value} stats: {len(normalized)} fields")
        return normalized

    def get_display_stats_for_position(self, position: str) -> Dict[str, str]:
        """
        Get position-specific stats to display in UI

        Args:
            position: Player position (QB, RB, WR, TE, K, DEF)

        Returns:
            Dict mapping canonical field names to display labels
        """
        position = position.upper()

        if position == 'QB':
            return {
                'pass_yds': 'Pass Yds',
                'pass_tds': 'Pass TDs',
                'pass_ints': 'INTs',
                'rush_yds': 'Rush Yds',
                'rush_tds': 'Rush TDs'
            }
        elif position in ['RB', 'FB']:
            return {
                'rush_yds': 'Rush Yds',
                'rush_tds': 'Rush TDs',
                'rec_yds': 'Rec Yds',
                'rec_tds': 'Rec TDs',
                'rec': 'Receptions'
            }
        elif position in ['WR', 'TE']:
            return {
                'rec_yds': 'Rec Yds',
                'rec_tds': 'Rec TDs',
                'rec': 'Receptions',
                'rush_yds': 'Rush Yds',
                'rush_tds': 'Rush TDs'
            }
        elif position == 'K':
            return {
                'fgm': 'FG Made',
                'fga': 'FG Att',
                'xpm': 'XP Made',
                'fgm_40_49': 'FG 40-49',
                'fgm_50_59': 'FG 50+'
            }
        elif position in ['DEF', 'DST']:
            return {
                'def_sack': 'Sacks',
                'def_int': 'INTs',
                'def_fumble_rec': 'Fum Rec',
                'def_td': 'Def TDs',
                'pts_allow': 'Pts Allow'
            }
        else:
            return {}

    def validate_stat_mapping(self, stat_type: StatType) -> Dict[str, Any]:
        """
        Validate that a stat mapping has all necessary fields

        Returns:
            Dict with validation results
        """
        mapping = self.MAPPINGS.get(stat_type, {})

        # Check for common missing fields by position
        missing_fields = []

        # Basic offensive stats
        required_offensive = ['pass_yds', 'pass_tds', 'rush_yds', 'rush_tds', 'rec_yds', 'rec_tds', 'rec']
        for field in required_offensive:
            if field not in mapping.values():
                missing_fields.append(f"Missing {field} mapping")

        return {
            'stat_type': stat_type.value,
            'total_mappings': len(mapping),
            'missing_fields': missing_fields,
            'is_valid': len(missing_fields) == 0
        }


# Global instance
stat_mapper = StatMappingService()