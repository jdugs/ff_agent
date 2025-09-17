from sqlalchemy import Column, String, Integer, Enum, DECIMAL, DateTime, JSON, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base, TimestampMixin

class SleeperLeague(Base, TimestampMixin):
    __tablename__ = "sleeper_leagues"
    
    league_id = Column(String(50), primary_key=True)
    user_id = Column(String(50), nullable=False, index=True)
    sleeper_user_id = Column(String(50), nullable=False)
    league_name = Column(String(100))
    season = Column(String(10), nullable=False, index=True)
    status = Column(Enum('pre_draft', 'drafting', 'in_season', 'complete', name='league_status'), default='in_season')
    sport = Column(String(20), default='nfl')
    settings = Column(JSON)
    scoring_settings = Column(JSON)
    roster_positions = Column(JSON)
    total_rosters = Column(Integer)
    draft_id = Column(String(50))
    previous_league_id = Column(String(50))
    last_synced = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    rosters = relationship("SleeperRoster", back_populates="league")
    matchups = relationship("SleeperMatchup", back_populates="league")

class SleeperRoster(Base, TimestampMixin):
    __tablename__ = "sleeper_rosters"
    
    roster_id = Column(Integer, nullable=False, primary_key=True)
    league_id = Column(String(50), ForeignKey('sleeper_leagues.league_id'), nullable=False, primary_key=True, index=True)
    owner_id = Column(String(50), index=True)
    player_ids = Column(JSON)
    starters = Column(JSON)
    reserve = Column(JSON)
    taxi = Column(JSON)
    settings = Column(JSON)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    ties = Column(Integer, default=0)
    fpts = Column(DECIMAL(6, 2), default=0)
    fpts_against = Column(DECIMAL(6, 2), default=0)
    last_synced = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    league = relationship("SleeperLeague", back_populates="rosters")

class SleeperPlayer(Base, TimestampMixin):
    __tablename__ = "sleeper_players"
    
    sleeper_player_id = Column(String(50), primary_key=True)
    player_id = Column(String(50), ForeignKey('players.player_id'), index=True)  # Link to our players table
    full_name = Column(String(100), index=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    position = Column(String(10), index=True)
    team = Column(String(10), index=True)
    age = Column(Integer)
    height = Column(String(10))
    weight = Column(String(10))
    college = Column(String(100))
    years_exp = Column(Integer)
    status = Column(Enum('Active', 'Inactive', 'Injured Reserve', 'Reserve/PUP', name='player_status'), default='Active')
    fantasy_positions = Column(JSON)
    
    # External IDs for multi-source integration
    espn_id = Column(String(50), index=True)
    rotowire_id = Column(String(50), index=True)
    fantasy_data_id = Column(String(50), index=True)
    yahoo_id = Column(String(50), index=True)
    stats_id = Column(String(50), index=True)  # For stats.com or similar
    
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    player = relationship("Player")

class SleeperMatchup(Base, TimestampMixin):
    __tablename__ = "sleeper_matchups"
    
    matchup_id = Column(BigInteger, primary_key=True, autoincrement=True)
    league_id = Column(String(50), ForeignKey('sleeper_leagues.league_id'), nullable=False, index=True)
    week = Column(Integer, nullable=False, index=True)
    roster_id = Column(Integer, nullable=False, index=True)
    matchup_id_sleeper = Column(Integer)
    points = Column(DECIMAL(6, 2))
    points_for = Column(DECIMAL(6, 2))
    points_against = Column(DECIMAL(6, 2))
    starters = Column(JSON)
    starters_points = Column(JSON)
    players_points = Column(JSON)
    custom_points = Column(JSON)
    
    # Relationships
    league = relationship("SleeperLeague", back_populates="matchups")

class SleeperPlayerStats(Base, TimestampMixin):
    __tablename__ = "sleeper_player_stats"
    
    stat_id = Column(BigInteger, primary_key=True, autoincrement=True)
    sleeper_player_id = Column(String(50), ForeignKey('sleeper_players.sleeper_player_id'), nullable=False, index=True)
    week = Column(Integer, nullable=False, index=True)
    season = Column(String(10), nullable=False, index=True)
    
    # Fantasy points
    fantasy_points_ppr = Column(DECIMAL(5, 2))
    fantasy_points_standard = Column(DECIMAL(5, 2))
    fantasy_points_half_ppr = Column(DECIMAL(5, 2))
    
    # Passing stats
    pass_yds = Column(Integer)
    pass_tds = Column(Integer)
    pass_ints = Column(Integer)
    pass_att = Column(Integer)
    pass_cmp = Column(Integer)
    
    # Rushing stats
    rush_yds = Column(Integer)
    rush_tds = Column(Integer)
    rush_att = Column(Integer)
    
    # Receiving stats
    rec_yds = Column(Integer)
    rec_tds = Column(Integer)
    rec = Column(Integer)
    rec_tgt = Column(Integer)

    # 2-point conversions
    pass_2pt = Column(Integer)
    rush_2pt = Column(Integer)
    rec_2pt = Column(Integer)
    def_2pt = Column(Integer)

    # Fumbles and other penalties
    fum = Column(Integer)              # Fumbles (not lost)
    fum_lost = Column(Integer)         # Fumbles lost
    pass_sack = Column(DECIMAL(4, 1))  # Sacks taken by QB
    ff = Column(DECIMAL(4, 1))         # Forced fumbles
    fum_rec_td = Column(Integer)       # Fumble recovery touchdown

    # Position bonuses
    bonus_rec_te = Column(DECIMAL(4, 1))  # TE reception bonus
    
    # Kicking stats
    fgm = Column(Integer)
    fga = Column(Integer)
    xpm = Column(Integer)
    xpa = Column(Integer)

    # Distance-based field goal stats
    fgm_0_19 = Column(Integer)
    fgm_20_29 = Column(Integer)
    fgm_30_39 = Column(Integer)
    fgm_40_49 = Column(Integer)
    fgm_50_59 = Column(Integer)
    fgm_60p = Column(Integer)

    # Distance-based field goal misses
    fgmiss_0_19 = Column(Integer)
    fgmiss_20_29 = Column(Integer)
    fgmiss_30_39 = Column(Integer)
    fgmiss_40_49 = Column(Integer)

    # Kicking yards and misses
    fgm_yds = Column(Integer)    # Total field goal yards
    xpmiss = Column(Integer)     # Missed extra points
    
    # Defensive stats
    def_sack = Column(DECIMAL(4, 1))  # Sacks (can be fractional)
    def_int = Column(Integer)         # Interceptions
    def_fumble_rec = Column(Integer)  # Fumble recoveries
    def_td = Column(Integer)          # Defensive touchdowns
    def_safety = Column(Integer)      # Safeties
    def_block_kick = Column(Integer)  # Blocked kicks
    def_pass_def = Column(Integer)    # Pass deflections
    def_tackle_solo = Column(Integer) # Solo tackles
    def_tackle_assist = Column(Integer) # Assisted tackles
    def_qb_hit = Column(Integer)      # QB hits
    def_tfl = Column(Integer)         # Tackles for loss

    # Defense/Special Teams - Team Defense Stats
    pts_allow_0 = Column(Integer)      # Points allowed: 0
    pts_allow_1_6 = Column(Integer)    # Points allowed: 1-6
    pts_allow_7_13 = Column(Integer)   # Points allowed: 7-13
    pts_allow_14_20 = Column(Integer)  # Points allowed: 14-20
    pts_allow_21_27 = Column(Integer)  # Points allowed: 21-27
    pts_allow_28_34 = Column(Integer)  # Points allowed: 28-34
    pts_allow_35p = Column(Integer)    # Points allowed: 35+

    # Yards allowed tiers
    yds_allow_0_100 = Column(Integer)    # Yards allowed: 0-100
    yds_allow_100_199 = Column(Integer)  # Yards allowed: 100-199
    yds_allow_200_299 = Column(Integer)  # Yards allowed: 200-299
    yds_allow_300_349 = Column(Integer)  # Yards allowed: 300-349
    yds_allow_350_399 = Column(Integer)  # Yards allowed: 350-399
    yds_allow_400_449 = Column(Integer)  # Yards allowed: 400-449
    yds_allow_450_499 = Column(Integer)  # Yards allowed: 450-499
    yds_allow_500_549 = Column(Integer)  # Yards allowed: 500-549
    yds_allow_550p = Column(Integer)     # Yards allowed: 550+

    # Additional defensive stats
    def_4_and_stop = Column(Integer)   # 4th down stops
    def_st_td = Column(Integer)        # Special teams TD
    def_st_fum_rec = Column(Integer)   # Special teams fumble recovery
    def_st_ff = Column(DECIMAL(4, 1))  # Special teams forced fumble
    idp_tkl = Column(Integer)          # Individual defensive player tackles

    # Special teams return stats
    kr_yd = Column(Integer)            # Kick return yards
    pr_yd = Column(Integer)            # Punt return yards
    st_td = Column(Integer)            # Special teams touchdown
    st_fum_rec = Column(Integer)       # Special teams fumble recovery
    st_ff = Column(DECIMAL(4, 1))     # Special teams forced fumble

    # Additional team defense stats
    pts_allow = Column(DECIMAL(5, 2))  # Total points allowed (for -0.25 per point)
    yds_allow = Column(Integer)        # Total yards allowed (for -0.02 per yard)
    
    # Raw stats from Sleeper
    raw_stats = Column(JSON)
    
    # Relationships
    player = relationship("SleeperPlayer")

class SleeperPlayerProjections(Base, TimestampMixin):
    __tablename__ = "sleeper_player_projections"
    
    projection_id = Column(BigInteger, primary_key=True, autoincrement=True)
    sleeper_player_id = Column(String(50), ForeignKey('sleeper_players.sleeper_player_id'), nullable=False, index=True)
    week = Column(Integer, nullable=False, index=True)
    season = Column(String(10), nullable=False, index=True)
    
    # Projected fantasy points
    projected_points_ppr = Column(DECIMAL(5, 2))
    projected_points_standard = Column(DECIMAL(5, 2))
    projected_points_half_ppr = Column(DECIMAL(5, 2))
    
    # Projected stats (similar structure to actual stats)
    proj_pass_yds = Column(DECIMAL(5, 1))
    proj_pass_tds = Column(DECIMAL(3, 1))
    proj_rush_yds = Column(DECIMAL(5, 1))
    proj_rush_tds = Column(DECIMAL(3, 1))
    proj_rec_yds = Column(DECIMAL(5, 1))
    proj_rec_tds = Column(DECIMAL(3, 1))
    proj_rec = Column(DECIMAL(4, 1))
    
    # Raw projections from Sleeper
    raw_projections = Column(JSON)
    
    # Relationships
    player = relationship("SleeperPlayer")