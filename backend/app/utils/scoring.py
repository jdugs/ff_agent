"""
Shared fantasy scoring utilities to ensure consistent calculations across all APIs
"""
from typing import Dict, Optional

def safe_float(value):
    """Helper function to safely convert values to float"""
    if value is None:
        return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def calculate_stat_points(stats, scoring_settings: Dict, stat_mapping: Dict) -> float:
    """Calculate fantasy points using a stat mapping approach

    Args:
        stats: Either a database object with attributes or a dictionary
        scoring_settings: League scoring configuration
        stat_mapping: Map of stat_field -> scoring_key
    """
    total_points = 0.0

    for stat_field, scoring_key in stat_mapping.items():
        # Handle both database objects and dictionaries
        if hasattr(stats, stat_field):
            stat_value = safe_float(getattr(stats, stat_field, 0))
        else:
            stat_value = safe_float(stats.get(stat_field, 0))

        scoring_value = safe_float(scoring_settings.get(scoring_key, 0))
        points_added = stat_value * scoring_value
        total_points += points_added

    return total_points

def calculate_fantasy_points(
    stats,
    scoring_settings: Dict,
    player_position: Optional[str] = None,
    stat_type = None
) -> Dict[str, float]:
    """
    Calculate fantasy points using league-specific scoring settings

    Args:
        stats: Player stats object (from database, projections, etc.)
        scoring_settings: League scoring configuration
        player_position: Player position for position-specific bonuses
        stat_type: Type of stats for proper mapping (optional, auto-detected)

    Returns:
        Dict with ppr, standard, and half_ppr point totals
    """
    if not stats or not scoring_settings:
        return {'ppr': 0.0, 'standard': 0.0, 'half_ppr': 0.0}

    # Use unified stat mapping if stat_type is provided
    if stat_type:
        from app.services.stat_mapping_service import stat_mapper
        normalized_stats = stat_mapper.normalize_stats(stats, stat_type, player_position)
        stats = normalized_stats

    # Define comprehensive stat mapping: stat_field -> scoring_setting_key
    stat_mapping = {
        # Passing stats
        'pass_yds': 'pass_yd',
        'pass_tds': 'pass_td',
        'pass_ints': 'pass_int',
        'pass_sack': 'pass_sack',
        'pass_2pt': 'pass_2pt',

        # Rushing stats
        'rush_yds': 'rush_yd',
        'rush_tds': 'rush_td',
        'rush_2pt': 'rush_2pt',

        # Receiving stats
        'rec_yds': 'rec_yd',
        'rec_tds': 'rec_td',
        'rec_2pt': 'rec_2pt',

        # Fumbles
        'fum_lost': 'fum_lost',

        # Kicker stats
        'fgm': 'fgm',
        'fga': 'fga',
        'xpm': 'xpm',
        'xpa': 'xpa',
        'xpmiss': 'xpmiss',
        'fgm_yds': 'fgm_yds',  # Field goal yards

        # Distance-based field goals
        'fgm_0_19': 'fgm_0_19',
        'fgm_20_29': 'fgm_20_29',
        'fgm_30_39': 'fgm_30_39',
        'fgm_40_49': 'fgm_40_49',
        'fgm_50_59': 'fgm_50_59',
        'fgm_60p': 'fgm_60p',

        # Field goal misses
        'fgmiss_0_19': 'fgmiss_0_19',
        'fgmiss_20_29': 'fgmiss_20_29',
        'fgmiss_30_39': 'fgmiss_30_39',
        'fgmiss_40_49': 'fgmiss_40_49',

        # Defense stats
        'def_sack': 'sack',
        'def_int': 'int',
        'def_fumble_rec': 'fum_rec',
        'def_td': 'def_td',
        'def_safety': 'safe',
        'def_block_kick': 'blk_kick',
        'def_4_and_stop': 'def_4_and_stop',

        # Points allowed tiers
        'pts_allow_0': 'pts_allow_0',
        'pts_allow_1_6': 'pts_allow_1_6',
        'pts_allow_7_13': 'pts_allow_7_13',
        'pts_allow_14_20': 'pts_allow_14_20',
        'pts_allow_21_27': 'pts_allow_21_27',
        'pts_allow_28_34': 'pts_allow_28_34',
        'pts_allow_35p': 'pts_allow_35p',

        # Yards allowed tiers
        'yds_allow_0_100': 'yds_allow_0_100',
        'yds_allow_100_199': 'yds_allow_100_199',
        'yds_allow_200_299': 'yds_allow_200_299',
        'yds_allow_300_349': 'yds_allow_300_349',
        'yds_allow_350_399': 'yds_allow_350_399',
        'yds_allow_400_449': 'yds_allow_400_449',
        'yds_allow_450_499': 'yds_allow_450_499',
        'yds_allow_500_549': 'yds_allow_500_549',
        'yds_allow_550p': 'yds_allow_550p',

        # Continuous defense scoring
        'pts_allow': 'pts_allow',  # Total points allowed (continuous penalty)
        'yds_allow': 'yds_allow',  # Total yards allowed (continuous penalty)

        # Special teams
        'st_td': 'st_td',
        'def_st_td': 'def_st_td',
        'st_fum_rec': 'st_fum_rec',
        'def_st_fum_rec': 'def_st_fum_rec',
        'st_ff': 'st_ff',
        'def_st_ff': 'def_st_ff',
        'kr_yd': 'kr_yd',
        'pr_yd': 'pr_yd',

        # Additional stats
        'fum': 'fum',
        'ff': 'ff',
        'fum_rec_td': 'fum_rec_td',
        'idp_tkl': 'idp_tkl',
        'def_pass_def': 'def_pass_def',
        'def_tackle_solo': 'def_tackle_solo',
        'def_tackle_assist': 'def_tackle_assist',
        'def_qb_hit': 'def_qb_hit',
        'def_tfl': 'def_tfl',

        # Offensive player defensive stats (turnovers/tackles)
        'tkl': 'tkl',                    # Tackles by offensive players
        'tkl_solo': 'tkl_solo',          # Solo tackles by offensive players
        'tkl_ast': 'tkl_ast'             # Tackle assists by offensive players
    }

    # Calculate points using the mapping
    points = calculate_stat_points(stats, scoring_settings, stat_mapping)

    # Handle PPR separately (reception points)
    if hasattr(stats, 'rec'):
        receptions = safe_float(getattr(stats, 'rec', 0))
    else:
        receptions = safe_float(stats.get('rec', 0))

    base_rec_points = receptions * safe_float(scoring_settings.get('rec', 0))
    te_bonus = receptions * safe_float(scoring_settings.get('bonus_rec_te', 0)) if player_position == 'TE' else 0

    total_points = points + base_rec_points + te_bonus

    return {
        'ppr': round(total_points, 2),
        'standard': round(total_points - base_rec_points - te_bonus, 2),
        'half_ppr': round(total_points - (base_rec_points + te_bonus) * 0.5, 2)
    }