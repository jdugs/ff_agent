import axios from 'axios';
import type { TeamDashboard, League, DashboardStats, Player } from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.request.use((config) => {
  console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
  return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export class ApiClient {
  // Dashboard
  static async getDashboardStats(): Promise<DashboardStats> {
    const response = await api.get('/api/v1/dashboard/stats');
    return response.data;
  }

  // Sleeper Integration
  static async searchUser(username: string) {
    const response = await api.get(`/api/v1/sleeper/user/search/${username}`);
    return response.data;
  }

  static async getUserLeagues(userId: string): Promise<League[]> {
    const response = await api.get(`/api/v1/sleeper/user/${userId}/leagues`);
    return response.data;
  }

  static async syncUserLeagues(userId: string, season: string = '2025') {
    const response = await api.post(`/api/v1/sleeper/user/${userId}/sync?season=${season}`);
    return response.data;
  }

  static async syncLeague(leagueId: string, userId: string) {
    const response = await api.post(`/api/v1/sleeper/league/${leagueId}/sync?user_id=${userId}`);
    return response.data;
  }

  // Team Dashboard
  static async getTeamDashboard(leagueId: string, userId: string, week?: number): Promise<TeamDashboard> {
    const params = new URLSearchParams({
      league_id: leagueId,
      owner_id: userId,
      include_stats: 'true',
      include_news: 'false', 
      include_photos: 'false'
    });
    
    if (week) {
      params.append('week', week.toString());
    }
    
    const response = await api.get(`/api/v1/dashboard/roster?${params}`);
    return response.data;
  }

  // Player Data
  static async getPlayer(playerId: string): Promise<Player> {
    const response = await api.get(`/api/v1/players/${playerId}`);
    return response.data;
  }

  static async getPlayerRankings(playerId: string, week?: number, year: number = 2025) {
    const params = new URLSearchParams({ year: year.toString() });
    if (week) params.append('week', week.toString());
    
    const response = await api.get(`/api/v1/players/${playerId}/rankings?${params}`);
    return response.data;
  }

  // Matchups
  static async getMyMatchup(leagueId: string, week: number, userId: string) {
    const response = await api.get(`/api/v1/sleeper/league/${leagueId}/my-matchup/${week}?user_id=${userId}`);
    return response.data;
  }

  // Health Check
  static async healthCheck() {
    const response = await api.get('/health');
    return response.data;
  }
}