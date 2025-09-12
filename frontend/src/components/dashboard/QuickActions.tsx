'use client';

import React from 'react';
import type { TeamDashboard } from '@/lib/types';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useTeamStore } from '@/store/teamStore';
import { Settings, Shuffle, Users, RefreshCw } from 'lucide-react';

interface QuickActionsProps {
  team: TeamDashboard;
}

export const QuickActions: React.FC<QuickActionsProps> = ({ team }) => {
  const { syncLeague, selectedLeagueId, selectedUserId, isSyncing } = useTeamStore();

  const handleSync = () => {
    if (selectedLeagueId && selectedUserId) {
      syncLeague(selectedLeagueId, selectedUserId);
    }
  };

  return (
    <Card>
      <h3 className="text-lg font-semibold text-white mb-4">Quick Actions</h3>
      
      <div className="space-y-3">
        <Button 
          variant="primary" 
          className="w-full justify-start"
          onClick={handleSync}
          isLoading={isSyncing}
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Sync Latest Data
        </Button>
        
        <Button variant="secondary" className="w-full justify-start">
          <Shuffle className="w-4 h-4 mr-2" />
          Optimize Lineup
        </Button>
        
        <Button variant="secondary" className="w-full justify-start">
          <Users className="w-4 h-4 mr-2" />
          Trade Finder
        </Button>
        
        <Button variant="secondary" className="w-full justify-start">
          <Settings className="w-4 h-4 mr-2" />
          Waiver Wire
        </Button>
      </div>

      {/* Team Summary */}
      <div className="mt-6 pt-4 border-t border-dark-700">
        <div className="text-sm space-y-2">
          <div className="flex justify-between">
            <span className="text-dark-400">Starters:</span>
            <span className="text-success-400">{team.data.roster_summary.starters_count}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-dark-400">Bench:</span>
            <span className="text-warning-400">{team.data.roster_summary.bench_count}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-dark-400">Total Players:</span>
            <span className="text-primary-400">{team.data.roster_summary.total_players}</span>
          </div>
        </div>
      </div>
    </Card>
  );
};