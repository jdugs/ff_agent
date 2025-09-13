'use client';

import React, { useEffect, useState } from 'react';
import type { Matchup } from '@/lib/types';
import { useTeamStore } from '@/store/teamStore';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ApiClient } from '@/lib/api';
import { formatPoints } from '@/lib/utils';
import { TrendingUp, TrendingDown, Minus, Users } from 'lucide-react';

export const CurrentMatchup: React.FC = () => {
  const { selectedLeagueId, selectedUserId, currentWeek } = useTeamStore();
  const [matchup, setMatchup] = useState<Matchup | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (selectedLeagueId && selectedUserId && currentWeek) {
      loadMatchup();
    }
  }, [selectedLeagueId, selectedUserId, currentWeek]);

  const loadMatchup = async () => {
    if (!selectedLeagueId || !selectedUserId) return;

    setLoading(true);
    setError(null);

    try {
      const matchupData = await ApiClient.getMyMatchup(
        selectedLeagueId,
        currentWeek,
        selectedUserId
      );
      setMatchup(matchupData);
    } catch (err) {
      console.error('Failed to load matchup:', err);
      setError('Failed to load matchup data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Card>
        <div className="flex items-center justify-center py-8">
          <LoadingSpinner size="md" />
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <div className="text-center py-8 text-danger-400">
          <p>{error}</p>
        </div>
      </Card>
    );
  }

  if (!matchup) {
    return (
      <Card>
        <div className="text-center py-8 text-dark-400">
          <p>No matchup data available</p>
        </div>
      </Card>
    );
  }

  const myPoints = matchup.my_roster.points;
  const opponentPoints = matchup.opponent_roster?.points || 0;
  const pointDiff = myPoints - opponentPoints;

  const getMatchupStatus = () => {
    if (!matchup.is_complete) return 'in_progress';
    if (pointDiff > 0) return 'winning';
    if (pointDiff < 0) return 'losing';
    return 'tied';
  };

  const status = getMatchupStatus();

  const getStatusIcon = () => {
    switch (status) {
      case 'winning':
        return <TrendingUp className="w-5 h-5 text-success-400" />;
      case 'losing':
        return <TrendingDown className="w-5 h-5 text-danger-400" />;
      case 'tied':
        return <Minus className="w-5 h-5 text-warning-400" />;
      default:
        return <Users className="w-5 h-5 text-primary-400" />;
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'winning':
        return 'text-success-400';
      case 'losing':
        return 'text-danger-400';
      case 'tied':
        return 'text-warning-400';
      default:
        return 'text-primary-400';
    }
  };

  return (
    <Card>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white flex items-center">
          {getStatusIcon()}
          <span className="ml-2">Week {matchup.week} Matchup</span>
        </h3>
        <Badge 
          variant={
            status === 'winning' ? 'success' :
            status === 'losing' ? 'danger' :
            status === 'tied' ? 'warning' : 'info'
          }
          size="sm"
        >
          {matchup.is_complete ? 'Complete' : 'In Progress'}
        </Badge>
      </div>

      <div className="space-y-4">
        {/* Score comparison */}
        <div className="flex items-center justify-between p-4 bg-dark-700 rounded-lg">
          <div className="text-center">
            <div className="text-2xl font-bold text-white">
              {formatPoints(myPoints)}
            </div>
            <div className="text-xs text-success-400">
              Proj: {formatPoints(matchup.my_roster.projected_total)}
            </div>
            <div className="text-sm text-dark-400">You</div>
            <div className="text-xs text-dark-500">{matchup.my_roster.record}</div>
          </div>
          
          <div className="text-center">
            <div className="text-sm text-dark-400 mb-1">vs</div>
            <div className={`text-lg font-medium ${getStatusColor()}`}>
              {pointDiff > 0 ? `+${formatPoints(Math.abs(pointDiff))}` : 
               pointDiff < 0 ? `-${formatPoints(Math.abs(pointDiff))}` : 
               'Tied'}
            </div>
            {matchup.opponent_roster && (
              <div className="text-xs text-warning-400 mt-1">
                Proj Diff: {formatPoints(matchup.my_roster.projected_total - matchup.opponent_roster.projected_total)}
              </div>
            )}
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-white">
              {formatPoints(opponentPoints)}
            </div>
            {matchup.opponent_roster && (
              <div className="text-xs text-success-400">
                Proj: {formatPoints(matchup.opponent_roster.projected_total)}
              </div>
            )}
            <div className="text-sm text-dark-400">
              {matchup.opponent_roster ? 'Opponent' : 'Bye Week'}
            </div>
            <div className="text-xs text-dark-500">
              {matchup.opponent_roster?.record || 'N/A'}
            </div>
          </div>
        </div>

        {/* Opponent Roster */}
        {matchup.opponent_roster && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium text-white">Opponent's Lineup</h4>
              <div className="text-sm text-dark-400">
                Projected: {formatPoints(matchup.opponent_roster.projected_total)}
              </div>
            </div>
            <div className="max-h-48 overflow-y-auto space-y-1">
              {matchup.opponent_roster.players.map((player) => (
                <div key={player.sleeper_id} className="flex items-center justify-between text-xs p-2 bg-dark-800 rounded">
                  <div className="flex items-center space-x-2 min-w-0 flex-1">
                    <span className="text-primary-400 font-mono text-[10px] w-6 text-center">
                      {player.position}
                    </span>
                    <span className="text-white truncate">
                      {player.player_name || 'Unknown'}
                    </span>
                    <span className="text-dark-500 text-[10px]">
                      {player.team}
                    </span>
                  </div>
                  <div className="text-success-400 font-medium ml-2">
                    {player.projections ? formatPoints(player.projections.fantasy_points) : '0.0'}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Additional matchup info */}
        {matchup.opponent_roster && (
          <div className="text-center text-sm">
            <div className="text-dark-400">
              Matchup ID: {matchup.matchup_id}
            </div>
            {!matchup.is_complete && (
              <div className="text-warning-400 mt-1">
                <span className="inline-block w-2 h-2 bg-warning-400 rounded-full animate-pulse mr-1"></span>
                Game in progress
              </div>
            )}
          </div>
        )}

        {/* Bye week message */}
        {!matchup.opponent_roster && (
          <div className="text-center py-4 text-dark-400">
            <p className="text-lg">🏖️ Bye Week</p>
            <p className="text-sm">Enjoy your week off!</p>
          </div>
        )}
      </div>
    </Card>
  );
};