'use client';

import React, { useEffect } from 'react';
import { useTeamStore } from '@/store/teamStore';
import { useUIStore } from '@/store/uiStore';
import { TeamOverview } from '@/components/dashboard/TeamOverview';
import { StartingLineup } from '@/components/dashboard/StartingLineup';
import { QuickActions } from '@/components/dashboard/QuickActions';
import { RecentNews } from '@/components/dashboard/RecentNews';
import { WaiverTargets } from '@/components/dashboard/WaiverTargets';
import { Card } from '@/components/ui/Card';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

export default function DashboardPage() {
  const { 
    currentTeam, 
    isLoadingTeam, 
    selectedLeagueId, 
    selectedUserId,
    loadUserLeagues 
  } = useTeamStore();
  
  const { setPageLoading } = useUIStore();

  // Mock user ID for testing - replace with actual auth
  const testUserId = "1180399895784771584";

  useEffect(() => {
    setPageLoading(true);
    
    // Auto-load leagues for test user
    if (testUserId && !selectedLeagueId) {
      loadUserLeagues(testUserId);
    }
    
    setPageLoading(false);
  }, [testUserId, selectedLeagueId, loadUserLeagues, setPageLoading]);

  if (isLoadingTeam) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-center">
          <LoadingSpinner size="lg" />
          <p className="mt-4 text-dark-400">Loading your team...</p>
        </div>
      </div>
    );
  }

  if (!currentTeam) {
    return (
      <div className="p-6">
        <Card className="text-center py-12">
          <h2 className="text-xl font-semibold text-white mb-2">
            Welcome to Fantasy Dashboard
          </h2>
          <p className="text-dark-400 mb-6">
            Select a league from the sidebar to get started
          </p>
          {!selectedUserId && (
            <p className="text-sm text-warning-400">
              Please configure your Sleeper user ID in the code
            </p>
          )}
        </Card>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Team Overview Row */}
      <TeamOverview team={currentTeam} />

      {/* Starting Lineup */}
      <StartingLineup players={currentTeam.starters} />

      {/* Bottom Row - Actions, News, Waiver */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <QuickActions team={currentTeam} />
        <RecentNews players={currentTeam.starters} />
        <WaiverTargets />
      </div>
    </div>
  );
}