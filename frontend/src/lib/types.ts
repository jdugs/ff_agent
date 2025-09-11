export interface Player {
    sleeper_id: string;
    name: string;
    position: string;
    team: string;
    is_starter: boolean;
    rankings: PlayerRankingData[];
    consensus_rank?: number;
    rank_trend?: 'up' | 'down' | 'stable';
    latest_projection?: number;
    projection_range?: {
      min: number;
      max: number;
      avg: number;
    };
    recent_news: PlayerNewsData[];
    injury_status?: string;
    red_flags: string[];
    start_sit_recommendation?: 'start' | 'flex' | 'sit';
    confidence_score?: number;
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
    league_id: string;
    league_name: string;
    team_record: string;
    points_for: number;
    league_rank?: number;
    starters: Player[];
    bench: Player[];
    team_summary: {
      total_players: number;
      players_with_rankings: number;
      ranking_coverage: string;
      total_red_flags: number;
      injured_starters: number;
      projected_points?: number;
      team_health: 'good' | 'monitor' | 'concerning';
    };
    weekly_outlook: {
      week: number;
      outlook: 'strong' | 'moderate' | 'concerning';
      strong_starts: number;
      flex_plays: number;
      concerning_starts: number;
      avg_confidence: number;
      recommendations: string[];
    };
    last_synced: string;
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