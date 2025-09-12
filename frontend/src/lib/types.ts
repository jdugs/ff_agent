export interface Player {
    sleeper_id: string;
    player_name: string;
    position: string;
    team: string;
    is_starter: boolean;
    player_details: {
      age: number | null;
      height: string | null;
      weight: string | null;
      college: string | null;
      years_exp: number | null;
      status: string;
      fantasy_positions: string[];
    };
    external_ids: {
      espn_id: string | null;
      rotowire_id: string | null;
      fantasy_data_id: string | null;
      yahoo_id: string | null;
      stats_id: string | null;
    };
    projections: PlayerProjections | null;
    actual_stats: PlayerStats | null;
    news_alerts?: PlayerNews[];
    media?: PlayerMedia;
    // Legacy fields for backward compatibility
    rankings?: PlayerRankingData[];
    consensus_rank?: number;
    rank_trend?: 'up' | 'down' | 'stable';
    latest_projection?: number;
    projection_range?: {
      min: number;
      max: number;
      avg: number;
    };
    recent_news?: PlayerNewsData[];
    injury_status?: string;
    red_flags?: string[];
    start_sit_recommendation?: 'start' | 'flex' | 'sit';
    confidence_score?: number;
  }

  export interface PlayerProjections {
    fantasy_points: number;
    passing: {
      yards: number;
      touchdowns: number;
      interceptions: number;
    };
    rushing: {
      yards: number;
      touchdowns: number;
    };
    receiving: {
      yards: number;
      touchdowns: number;
      receptions: number;
    };
    meta: {
      provider_count: number;
      confidence_score: number;
      last_updated: string;
    };
  }

  export interface PlayerStats {
    fantasy_points: {
      ppr: number;
      standard: number;
      half_ppr: number;
    };
    passing: {
      yards: number;
      touchdowns: number;
      interceptions: number;
      attempts: number;
      completions: number;
    };
    rushing: {
      yards: number;
      touchdowns: number;
      attempts: number;
    };
    receiving: {
      yards: number;
      touchdowns: number;
      receptions: number;
      targets: number;
    };
    performance: {
      vs_projection: number | null;
    };
  }

  export interface PlayerNews {
    title: string;
    type: string;
    severity: 'high' | 'medium' | 'low';
    timestamp: string;
  }

  export interface PlayerMedia {
    headshot_url: string | null;
    team_logo_url: string | null;
  }
  
  export interface PlayerRankingData {
    source_name: string;
    position_rank?: number;
    overall_rank?: number;
    projection?: number;
    tier?: number;
    confidence: string;
    timestamp: string;
  }
  
  export interface PlayerNewsData {
    title: string;
    event_type: string;
    severity: string;
    description?: string;
    timestamp: string;
    source_name: string;
  }
  
  export interface TeamDashboard {
    success: boolean;
    data: {
      roster_summary: {
        league_id: string;
        owner_id: string;
        total_players: number;
        starters_count: number;
        bench_count: number;
        team_record: {
          wins: number;
          losses: number;
          ties: number;
          points_for: number;
          points_against: number;
        };
        projected_points_total: number;
        actual_points_total: number | null;
        performance_vs_projection: number | null;
      };
      lineup: {
        starters: Player[];
        bench: Player[];
      };
      quick_stats: {
        top_performer: Player | null;
        positions_summary: Record<string, number>;
      };
      metadata: {
        week: number | null;
        season: string;
        data_includes: {
          projections: boolean;
          actual_stats: boolean;
          bench_players: boolean;
          news_alerts: boolean;
          player_photos: boolean;
        };
        generated_at: string;
        last_roster_sync: string | null;
      };
    };
  }
  
  export interface League {
    league_id: string;
    league_name: string;
    season: string;
    status: string;
    total_rosters: number;
  }
  
  export interface DashboardStats {
    total_players: number;
    total_sources: number;
    total_rankings: number;
    active_sources: number;
    sleeper_leagues: number;
    sleeper_players: number;
  }
  
  // UI State types
  export interface UIState {
    selectedPlayer: Player | null;
    isPlayerModalOpen: boolean;
    isLoading: boolean;
    selectedLeague: string | null;
    currentWeek: number;
  }