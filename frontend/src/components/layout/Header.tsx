'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import { useTeamStore } from '@/store/teamStore';
import { useUIStore } from '@/store/uiStore';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Menu, RefreshCw, Settings, Bell } from 'lucide-react';

export const Header: React.FC = () => {
  const { 
    currentTeam, 
    leagues, 
    selectedLeagueId, 
    isSyncing, 
    syncLeague, 
    selectedUserId 
  } = useTeamStore();
  
  const { toggleSidebar } = useUIStore();

  const selectedLeague = leagues.find(l => l.league_id === selectedLeagueId);

  const handleSync = () => {
    if (selectedLeagueId && selectedUserId) {
      syncLeague(selectedLeagueId, selectedUserId);
    }
  };

  return (
    <header className="bg-dark-900 border-b border-dark-700 sticky top-0 z-40">
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Left side */}
          <div className="flex items-center space-x-4">
            <button
              onClick={toggleSidebar}
              className="text-dark-400 hover:text-white transition-colors md:hidden"
            >
              <Menu size={24} />
            </button>
            
            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">FF</span>
                </div>
                <h1 className="text-xl font-bold text-white hidden sm:block">
                  Fantasy Dashboard
                </h1>
              </div>
              
              {selectedLeague && (
                <div className="hidden md:flex items-center space-x-2">
                  <span className="text-dark-400">|</span>
                  <Badge variant="info" size="sm">
                    {selectedLeague.league_name}
                  </Badge>
                </div>
              )}
            </div>
          </div>

          {/* Center - Team Summary */}
          {currentTeam && (
            <div className="hidden lg:flex items-center space-x-6 text-sm">
              <div className="flex items-center space-x-2">
                <span className="text-dark-400">Record:</span>
                <span className="text-white font-medium">
                  {currentTeam.data.roster_summary.team_record.wins}-{currentTeam.data.roster_summary.team_record.losses}
                  {currentTeam.data.roster_summary.team_record.ties > 0 && `-${currentTeam.data.roster_summary.team_record.ties}`}
                </span>
              </div>
              
              <div className="flex items-center space-x-2">
                <span className="text-dark-400">Projected:</span>
                <span className="text-success-400 font-medium">
                  {currentTeam.data.roster_summary.projected_points_total.toFixed(2)}
                </span>
              </div>
              
              <div className="flex items-center space-x-2">
                <span className="text-dark-400">Points For:</span>
                <span className="text-white font-medium">
                  {currentTeam.data.roster_summary.team_record.points_for.toFixed(2)}
                </span>
              </div>
            </div>
          )}

          {/* Right side */}
          <div className="flex items-center space-x-3">
            {/* Sync button */}
            <Button
              variant="ghost"
              size="sm"
              onClick={handleSync}
              isLoading={isSyncing}
              disabled={!selectedLeagueId}
              className="hidden sm:flex"
            >
              <RefreshCw size={16} className={cn(isSyncing && 'animate-spin')} />
              <span className="ml-2">Sync</span>
            </Button>

            {/* Notifications */}
            <button className="text-dark-400 hover:text-white transition-colors relative">
              <Bell size={20} />
              <span className="absolute -top-1 -right-1 w-3 h-3 bg-danger-500 rounded-full"></span>
            </button>

            {/* Settings */}
            <button className="text-dark-400 hover:text-white transition-colors">
              <Settings size={20} />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
