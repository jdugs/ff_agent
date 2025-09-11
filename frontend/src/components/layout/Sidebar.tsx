'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import { useTeamStore } from '@/store/teamStore';
import { useUIStore } from '@/store/uiStore';
import { Badge } from '@/components/ui/Badge';
import { 
  Home, 
  Users, 
  TrendingUp, 
  Calendar,
  Settings,
  ChevronRight,
  X
} from 'lucide-react';

const navigationItems = [
  { id: 'dashboard', label: 'Dashboard', icon: Home },
  { id: 'team', label: 'Team Analysis', icon: Users },
  { id: 'trends', label: 'Trends', icon: TrendingUp },
  { id: 'schedule', label: 'Schedule', icon: Calendar },
  { id: 'settings', label: 'Settings', icon: Settings },
];

export const Sidebar: React.FC = () => {
  const { leagues, selectedLeagueId, setSelectedLeague, selectedUserId } = useTeamStore();
  const { sidebarOpen, toggleSidebar, currentPage, setCurrentPage } = useUIStore();

  const handleLeagueSelect = (leagueId: string) => {
    if (selectedUserId) {
      setSelectedLeague(leagueId, selectedUserId);
    }
  };

  return (
    <>
      {/* Mobile backdrop */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={toggleSidebar}
        />
      )}

      {/* Sidebar */}
      <aside className={cn(
        'fixed top-16 left-0 h-[calc(100vh-4rem)] w-64 bg-dark-900 border-r border-dark-700 transform transition-transform duration-200 ease-in-out z-50',
        'md:translate-x-0 md:relative md:top-0 md:h-screen',
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      )}>
        <div className="flex flex-col h-full">
          {/* Close button for mobile */}
          <div className="flex justify-end p-4 md:hidden">
            <button
              onClick={toggleSidebar}
              className="text-dark-400 hover:text-white"
            >
              <X size={20} />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 pb-4">
            <div className="space-y-1">
              {navigationItems.map((item) => {
                const Icon = item.icon;
                const isActive = currentPage === item.id;

                return (
                  <button
                    key={item.id}
                    onClick={() => setCurrentPage(item.id)}
                    className={cn(
                      'w-full flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors',
                      isActive
                        ? 'bg-primary-600 text-white'
                        : 'text-dark-300 hover:text-white hover:bg-dark-800'
                    )}
                  >
                    <Icon size={18} className="mr-3" />
                    {item.label}
                  </button>
                );
              })}
            </div>

            {/* League Selector */}
            {leagues.length > 0 && (
              <div className="mt-8">
                <h3 className="px-3 mb-3 text-xs font-semibold text-dark-400 uppercase tracking-wider">
                  Leagues
                </h3>
                <div className="space-y-1">
                  {leagues.map((league) => (
                    <button
                      key={league.league_id}
                      onClick={() => handleLeagueSelect(league.league_id)}
                      className={cn(
                        'w-full flex items-center justify-between px-3 py-2 text-sm rounded-lg transition-colors',
                        selectedLeagueId === league.league_id
                          ? 'bg-dark-700 text-white'
                          : 'text-dark-300 hover:text-white hover:bg-dark-800'
                      )}
                    >
                      <div className="flex flex-col items-start">
                        <span className="font-medium">
                          {league.league_name}
                        </span>
                        <span className="text-xs text-dark-400">
                          {league.season} • {league.total_rosters} teams
                        </span>
                      </div>
                      {selectedLeagueId === league.league_id && (
                        <ChevronRight size={16} />
                      )}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </nav>

          {/* Footer */}
          <div className="p-4 border-t border-dark-700">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center">
                <span className="text-white text-sm font-medium">U</span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-white truncate">
                  User
                </div>
                <div className="text-xs text-dark-400 truncate">
                  {selectedUserId || 'No user selected'}
                </div>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};