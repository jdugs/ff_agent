'use client';

import React, { useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { ApiClient } from '@/lib/api';
import type { FantasyWeekState, FantasyWeekPhase } from '@/lib/types';

export const WeekStateBanner: React.FC = () => {
  const [weekState, setWeekState] = useState<FantasyWeekState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchWeekState = async () => {
    try {
      const state = await ApiClient.getFantasyWeekState();
      setWeekState(state);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch week state:', err);
      setError('Failed to load week state');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWeekState();
    
    // Set up auto-refresh based on week state
    let interval: NodeJS.Timeout;
    if (weekState?.should_auto_refresh) {
      interval = setInterval(fetchWeekState, weekState.refresh_frequency_seconds * 1000);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [weekState?.should_auto_refresh, weekState?.refresh_frequency_seconds]);

  const getPhaseColor = (phase: FantasyWeekPhase) => {
    const colors = {
      planning: 'bg-blue-600',
      early_games: 'bg-orange-600', 
      pre_games: 'bg-yellow-600',
      games_active: 'bg-red-600',
      post_games: 'bg-purple-600',
      waivers_processing: 'bg-green-600'
    };
    return colors[phase] || 'bg-gray-600';
  };

  const getUrgencyColor = (urgency: string) => {
    const colors = {
      low: 'text-blue-400',
      medium: 'text-yellow-400', 
      high: 'text-red-400'
    };
    return colors[urgency] || 'text-gray-400';
  };

  const formatTimeUntilTransition = (timeString: string) => {
    try {
      // Parse the time duration string (e.g., "2:30:45.123456")
      const match = timeString.match(/(\d+):(\d+):(\d+)/);
      if (match) {
        const hours = parseInt(match[1]);
        const minutes = parseInt(match[2]);
        
        if (hours > 0) {
          return `${hours}h ${minutes}m`;
        } else {
          return `${minutes}m`;
        }
      }
      return timeString;
    } catch {
      return timeString;
    }
  };

  if (loading) {
    return (
      <Card className="animate-pulse">
        <div className="h-16 bg-dark-700 rounded"></div>
      </Card>
    );
  }

  if (error || !weekState) {
    return (
      <Card className="border-danger-500">
        <div className="text-center py-4 text-danger-400">
          {error || 'Unable to load week state'}
        </div>
      </Card>
    );
  }

  return (
    <Card className={`${getPhaseColor(weekState.current_phase)} bg-opacity-10 border-opacity-50`}>
      <div className="flex items-center justify-between">
        {/* Left side - Phase info */}
        <div className="flex items-center space-x-4">
          <div className={`w-3 h-3 rounded-full ${getPhaseColor(weekState.current_phase)}`}></div>
          <div>
            <h3 className="text-white font-semibold text-lg">
              {weekState.phase_info.name}
            </h3>
            <p className="text-dark-300 text-sm">
              {weekState.phase_info.description}
            </p>
          </div>
        </div>

        {/* Right side - Status and timing */}
        <div className="text-right">
          <div className="flex items-center space-x-2 mb-1">
            <span className={`text-xs font-medium ${getUrgencyColor(weekState.phase_info.urgency)}`}>
              {weekState.phase_info.urgency.toUpperCase()} PRIORITY
            </span>
            {weekState.should_auto_refresh && (
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-xs text-green-400">LIVE</span>
              </div>
            )}
          </div>
          <div className="text-xs text-dark-400">
            Next: {weekState.next_phase.phase.replace('_', ' ')} in {formatTimeUntilTransition(weekState.next_phase.time_until_transition)}
          </div>
        </div>
      </div>

      {/* Priority actions */}
      <div className="mt-3 pt-3 border-t border-dark-700">
        <div className="flex flex-wrap gap-2">
          {weekState.phase_info.priority_actions.slice(0, 3).map((action, index) => (
            <span
              key={index}
              className="text-xs bg-dark-700 text-dark-300 px-2 py-1 rounded"
            >
              {action}
            </span>
          ))}
          {weekState.phase_info.priority_actions.length > 3 && (
            <span className="text-xs text-dark-500">
              +{weekState.phase_info.priority_actions.length - 3} more
            </span>
          )}
        </div>
      </div>
    </Card>
  );
};