import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import type { TeamDashboard, League } from '@/lib/types';
import { ApiClient } from '@/lib/api';

interface TeamState {
  // Data
  currentTeam: TeamDashboard | null;
  leagues: League[];
  selectedLeagueId: string | null;
  selectedUserId: string | null;
  currentWeek: number;
  
  // Loading states
  isLoading: boolean;
  isLoadingTeam: boolean;
  isLoadingLeagues: boolean;
  isSyncing: boolean;
  
  // Error states
  error: string | null;
  
  // Actions
  setSelectedLeague: (leagueId: string, userId: string) => void;
  setCurrentWeek: (week: number) => void;
  loadTeamDashboard: () => Promise<void>;
  loadUserLeagues: (userId: string) => Promise<void>;
  syncLeague: (leagueId: string, userId: string) => Promise<void>;
  clearError: () => void;
  reset: () => void;
}

export const useTeamStore = create<TeamState>()(
  subscribeWithSelector((set, get) => ({
    // Initial state
    currentTeam: null,
    leagues: [],
    selectedLeagueId: null,
    selectedUserId: null,
    currentWeek: getCurrentWeek(),
    isLoading: false,
    isLoadingTeam: false,
    isLoadingLeagues: false,
    isSyncing: false,
    error: null,

    // Actions
    setSelectedLeague: (leagueId: string, userId: string) => {
      set({ selectedLeagueId: leagueId, selectedUserId: userId });
      get().loadTeamDashboard();
    },

    setCurrentWeek: (week: number) => {
      set({ currentWeek: week });
      get().loadTeamDashboard();
    },

    loadTeamDashboard: async () => {
      const { selectedLeagueId, selectedUserId, currentWeek } = get();
      
      if (!selectedLeagueId || !selectedUserId) {
        set({ error: 'No league or user selected' });
        return;
      }

      set({ isLoadingTeam: true, error: null });

      try {
        const teamResponse = await ApiClient.getTeamDashboard(
          selectedLeagueId,
          selectedUserId,
          currentWeek
        );
        
        // Transform new API response to match current UI expectations
        const teamData: TeamDashboard = {
          success: teamResponse.success,
          data: teamResponse.data
        };
        
        set({ currentTeam: teamData, isLoadingTeam: false });
      } catch (error) {
        console.error('Failed to load team dashboard:', error);
        set({ 
          error: 'Failed to load team data', 
          isLoadingTeam: false 
        });
      }
    },

    loadUserLeagues: async (userId: string) => {
      set({ isLoadingLeagues: true, error: null });

      try {
        const leagues = await ApiClient.getUserLeagues(userId);
        set({ leagues, isLoadingLeagues: false });
        
        // Auto-select first league if none selected
        if (leagues.length > 0 && !get().selectedLeagueId) {
          get().setSelectedLeague(leagues[0].league_id, userId);
        }
      } catch (error) {
        console.error('Failed to load leagues:', error);
        set({ 
          error: 'Failed to load leagues', 
          isLoadingLeagues: false 
        });
      }
    },

    syncLeague: async (leagueId: string, userId: string) => {
      set({ isSyncing: true, error: null });

      try {
        await ApiClient.syncLeague(leagueId, userId);
        // Reload team data after sync
        await get().loadTeamDashboard();
        set({ isSyncing: false });
      } catch (error) {
        console.error('Failed to sync league:', error);
        set({ 
          error: 'Failed to sync league data', 
          isSyncing: false 
        });
      }
    },

    clearError: () => set({ error: null }),

    reset: () => set({
      currentTeam: null,
      leagues: [],
      selectedLeagueId: null,
      selectedUserId: null,
      error: null,
      isLoading: false,
      isLoadingTeam: false,
      isLoadingLeagues: false,
      isSyncing: false,
    }),
  }))
);

// Helper function to get current NFL week
function getCurrentWeek(): number {
    const now = new Date();
    const weekOfYear = Math.ceil(
      (now.getTime() - new Date(now.getFullYear(), 0, 1).getTime()) / 
      (7 * 24 * 60 * 60 * 1000)
    );
    
    // Rough estimate: NFL season starts around week 36
    if (weekOfYear < 30) return 1;
    if (weekOfYear > 52) return 18;
    return Math.max(1, Math.min(18, weekOfYear - 35));
  }
  