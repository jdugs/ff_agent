import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface SettingsState {
  // User preferences
  defaultUserId: string | null;
  defaultLeagueId: string | null;
  theme: 'dark' | 'light';
  
  // Dashboard preferences
  showProjections: boolean;
  showRankings: boolean;
  showNews: boolean;
  autoRefreshInterval: number; // minutes
  
  // Notification preferences
  enableNotifications: boolean;
  notifyOnPlayerNews: boolean;
  notifyOnRankingChanges: boolean;
  
  // Actions
  setDefaultUser: (userId: string) => void;
  setDefaultLeague: (leagueId: string) => void;
  setTheme: (theme: 'dark' | 'light') => void;
  updateDashboardPreferences: (preferences: Partial<Pick<SettingsState, 'showProjections' | 'showRankings' | 'showNews'>>) => void;
  setAutoRefreshInterval: (minutes: number) => void;
  updateNotificationPreferences: (preferences: Partial<Pick<SettingsState, 'enableNotifications' | 'notifyOnPlayerNews' | 'notifyOnRankingChanges'>>) => void;
  reset: () => void;
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      // Initial state
      defaultUserId: null,
      defaultLeagueId: null,
      theme: 'dark',
      showProjections: true,
      showRankings: true,
      showNews: true,
      autoRefreshInterval: 5,
      enableNotifications: true,
      notifyOnPlayerNews: true,
      notifyOnRankingChanges: false,

      // Actions
      setDefaultUser: (userId: string) => {
        set({ defaultUserId: userId });
      },

      setDefaultLeague: (leagueId: string) => {
        set({ defaultLeagueId: leagueId });
      },

      setTheme: (theme: 'dark' | 'light') => {
        set({ theme });
        // Apply theme to document
        if (typeof document !== 'undefined') {
          document.documentElement.classList.toggle('dark', theme === 'dark');
        }
      },

      updateDashboardPreferences: (preferences) => {
        set((state) => ({ ...state, ...preferences }));
      },

      setAutoRefreshInterval: (minutes: number) => {
        set({ autoRefreshInterval: minutes });
      },

      updateNotificationPreferences: (preferences) => {
        set((state) => ({ ...state, ...preferences }));
      },

      reset: () => {
        set({
          defaultUserId: null,
          defaultLeagueId: null,
          theme: 'dark',
          showProjections: true,
          showRankings: true,
          showNews: true,
          autoRefreshInterval: 5,
          enableNotifications: true,
          notifyOnPlayerNews: true,
          notifyOnRankingChanges: false,
        });
      },
    }),
    {
      name: 'fantasy-dashboard-settings',
      partialize: (state) => ({
        defaultUserId: state.defaultUserId,
        defaultLeagueId: state.defaultLeagueId,
        theme: state.theme,
        showProjections: state.showProjections,
        showRankings: state.showRankings,
        showNews: state.showNews,
        autoRefreshInterval: state.autoRefreshInterval,
        enableNotifications: state.enableNotifications,
        notifyOnPlayerNews: state.notifyOnPlayerNews,
        notifyOnRankingChanges: state.notifyOnRankingChanges,
      }),
    }
  )
);