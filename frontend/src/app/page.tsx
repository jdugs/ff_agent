'use client';

import React, { useEffect } from 'react';
import { useTeamStore } from '@/store/teamStore';
import { useUIStore } from '@/store/uiStore';
import { TeamOverview } from '@/components/dashboard/TeamOverview';
import { StartingLineup } from '@/components/dashboard/StartingLineup';
import { QuickActions } from '@/components/dashboard/QuickActions';
import { RecentNews } from '@/components/dashboard/RecentNews';
import { WaiverTargets } from '@/components/dashboard/WaiverTargets';
import { CurrentMatchup } from '@/components/dashboard/CurrentMatchup';
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
  
  const { setPageLoading, currentPage } = useUIStore();

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

  // Render different content based on current page
  const renderPageContent = () => {
    switch (currentPage) {
      case 'dashboard':
        return (
          <div className="p-6 space-y-6">
            {/* Team Overview and Current Matchup Row */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <TeamOverview team={currentTeam} />
              </div>
              <CurrentMatchup />
            </div>

            {/* Starting Lineup */}
            <StartingLineup players={currentTeam.data.lineup.starters} />

            {/* Bottom Row - Actions, News, Waiver */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <QuickActions team={currentTeam} />
              <RecentNews players={currentTeam.data.lineup.starters} />
              <WaiverTargets />
            </div>
          </div>
        );

      case 'team':
        return (
          <div className="p-6 space-y-6">
            <Card>
              <h2 className="text-2xl font-bold text-white mb-4">Team Analysis</h2>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Starting Lineup */}
                <div>
                  <h3 className="text-lg font-semibold text-white mb-3">Starting Lineup</h3>
                  <div className="space-y-3">
                    {currentTeam.data.lineup.starters.map((player) => (
                      <div key={player.sleeper_id} className="flex items-center justify-between p-3 bg-dark-700 rounded">
                        <div>
                          <span className="text-white font-medium">{player.player_name}</span>
                          <span className="text-dark-400 ml-2">({player.position} - {player.team})</span>
                        </div>
                        <div className="text-right">
                          <div className="text-success-400 font-medium">
                            {player.projections?.fantasy_points.toFixed(1) || '0.0'} pts
                          </div>
                          <div className="text-xs text-dark-400">
                            {player.projections?.meta.provider_count || 0} provider(s)
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Bench */}
                <div>
                  <h3 className="text-lg font-semibold text-white mb-3">Bench</h3>
                  <div className="space-y-3">
                    {currentTeam.data.lineup.bench.map((player) => (
                      <div key={player.sleeper_id} className="flex items-center justify-between p-3 bg-dark-800 rounded">
                        <div>
                          <span className="text-white font-medium">{player.player_name}</span>
                          <span className="text-dark-400 ml-2">({player.position} - {player.team})</span>
                        </div>
                        <div className="text-right">
                          <div className="text-warning-400 font-medium">
                            {player.projections?.fantasy_points.toFixed(1) || '0.0'} pts
                          </div>
                          <div className="text-xs text-dark-400">
                            {player.projections?.meta.provider_count || 0} provider(s)
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </Card>
          </div>
        );

      case 'trends':
        return (
          <div className="p-6">
            <Card>
              <h2 className="text-2xl font-bold text-white mb-4">Trends & Analytics</h2>
              <div className="text-center py-12 text-dark-400">
                <p className="text-lg">Trends analysis coming soon!</p>
                <p className="text-sm mt-2">This will show player performance trends, projection accuracy, and more.</p>
              </div>
            </Card>
          </div>
        );

      case 'schedule':
        return (
          <div className="p-6">
            <Card>
              <h2 className="text-2xl font-bold text-white mb-4">Schedule & Matchups</h2>
              <div className="text-center py-12 text-dark-400">
                <p className="text-lg">Schedule analysis coming soon!</p>
                <p className="text-sm mt-2">This will show upcoming matchups, strength of schedule, and opponent analysis.</p>
              </div>
            </Card>
          </div>
        );

      case 'settings':
        return (
          <div className="p-6">
            <Card>
              <h2 className="text-2xl font-bold text-white mb-4">Settings</h2>
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-white mb-3">League Information</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-dark-400">League ID:</span>
                      <span className="text-white">{selectedLeagueId}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Owner ID:</span>
                      <span className="text-white">{selectedUserId}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Total Players:</span>
                      <span className="text-white">{currentTeam.data.roster_summary.total_players}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Last Sync:</span>
                      <span className="text-white">
                        {currentTeam.data.metadata.last_roster_sync 
                          ? new Date(currentTeam.data.metadata.last_roster_sync).toLocaleDateString()
                          : 'Never'
                        }
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        );

      default:
        return (
          <div className="p-6">
            <Card>
              <div className="text-center py-12 text-dark-400">
                <p>Page not found</p>
              </div>
            </Card>
          </div>
        );
    }
  };

  return renderPageContent();
}