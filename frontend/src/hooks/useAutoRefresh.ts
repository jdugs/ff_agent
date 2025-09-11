import { useEffect, useRef } from 'react';
import { useTeamStore } from '@/store/teamStore';
import { useSettingsStore } from '@/store/settingsStore';

export const useAutoRefresh = () => {
  const { loadTeamDashboard, selectedLeagueId } = useTeamStore();
  const { autoRefreshInterval } = useSettingsStore();
  const intervalRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    if (!selectedLeagueId || autoRefreshInterval <= 0) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      return;
    }

    intervalRef.current = setInterval(() => {
      loadTeamDashboard();
    }, autoRefreshInterval * 60 * 1000); // Convert minutes to milliseconds

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [selectedLeagueId, autoRefreshInterval, loadTeamDashboard]);
};
