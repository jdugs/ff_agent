'use client';

import React from 'react';
import { Card } from '@/components/ui/Card';
import { useTeamStore } from '@/store/teamStore';
import type { Player } from '@/lib/types';

interface MatchupHeaderProps {
  userPlayers?: Player[];
  opponentPlayers?: Player[];
  isByeWeek?: boolean;
  selectedWeek?: number;
  currentWeek?: number;
  onWeekChange?: (week: number) => void;
}

export const MatchupHeader: React.FC<MatchupHeaderProps> = ({
  userPlayers,
  opponentPlayers,
  isByeWeek = false,
  selectedWeek,
  currentWeek: propCurrentWeek,
  onWeekChange
}) => {
  const { currentWeek: storeCurrentWeek } = useTeamStore();
  const currentWeek = propCurrentWeek || storeCurrentWeek;

  // Calculate user team totals
  const userTotals = React.useMemo(() => {
    if (!userPlayers?.length) return { projected: 0, actual: 0, hasActual: false };

    const starters = userPlayers.filter(p => p.is_starter);
    const projected = starters.reduce((sum, player) =>
      sum + (player.projections?.fantasy_points ?? 0), 0);
    const actual = starters.reduce((sum, player) =>
      sum + (player.actual_stats?.fantasy_points?.ppr ?? 0), 0);
    const hasActual = starters.some(player => player.actual_stats !== null);

    return { projected, actual, hasActual };
  }, [userPlayers]);

  // Calculate opponent totals
  const opponentTotals = React.useMemo(() => {
    if (isByeWeek || !opponentPlayers?.length) return { projected: 0, actual: 0, hasActual: false };

    const starters = opponentPlayers.filter(p => p.is_starter);
    const projected = starters.reduce((sum, player) =>
      sum + (player.projections?.fantasy_points ?? 0), 0);
    const actual = starters.reduce((sum, player) =>
      sum + (player.actual_stats?.fantasy_points?.ppr ?? 0), 0);
    const hasActual = starters.some(player => player.actual_stats !== null);

    return { projected, actual, hasActual };
  }, [opponentPlayers, isByeWeek]);

  if (isByeWeek) {
    return (
      <Card>
        <div className="text-center py-4">
          <h2 className="text-lg font-bold text-white mb-2">Week {currentWeek}</h2>
          <p className="text-dark-400">🏖️ Bye Week - No matchup this week</p>
        </div>
      </Card>
    );
  }

  const projectedDiff = userTotals.projected - opponentTotals.projected;
  const actualDiff = userTotals.actual - opponentTotals.actual;
  const showActual = userTotals.hasActual || opponentTotals.hasActual;

  // Determine if this is a completed matchup (past week with actual stats)
  const isCompletedMatchup = selectedWeek && currentWeek && selectedWeek < currentWeek && showActual;

  return (
    <Card>
      <div className="text-center py-3">
        {/* Header with Week Selector */}
        <div className="flex justify-between items-center mb-3">
          <h3 className="text-sm font-medium text-white">Your Team</h3>

          {/* Compact Week Selector */}
          {onWeekChange ? (
            <div className="flex items-center space-x-2">
              <button
                onClick={() => onWeekChange(Math.max(1, (selectedWeek || currentWeek || 1) - 1))}
                disabled={(selectedWeek || currentWeek || 1) <= 1}
                className="w-6 h-6 flex items-center justify-center bg-dark-700 text-white rounded text-xs hover:bg-dark-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                ←
              </button>
              <select
                value={selectedWeek || currentWeek || 1}
                onChange={(e) => onWeekChange(Number(e.target.value))}
                className="px-2 py-1 bg-dark-700 text-white rounded text-xs border border-dark-600 focus:border-primary-500 min-w-16"
              >
                {Array.from({ length: 18 }, (_, i) => i + 1).map(week => (
                  <option key={week} value={week}>
                    Week {week}
                  </option>
                ))}
              </select>
              <button
                onClick={() => onWeekChange(Math.min(18, (selectedWeek || currentWeek || 1) + 1))}
                disabled={(selectedWeek || currentWeek || 1) >= 18}
                className="w-6 h-6 flex items-center justify-center bg-dark-700 text-white rounded text-xs hover:bg-dark-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                →
              </button>
            </div>
          ) : (
            <div className="text-xs text-dark-400">Week {selectedWeek || currentWeek}</div>
          )}

          <h3 className="text-sm font-medium text-white">Opponent</h3>
        </div>

        {/* Main Scores */}
        <div className="flex justify-between items-center">
          {/* Your Score */}
          <div className="text-center flex-1">
            <div className="text-2xl font-bold text-white">
              {showActual ? userTotals.actual.toFixed(1) : userTotals.projected.toFixed(1)}
            </div>
            {showActual && (
              <div className="text-xs text-dark-400">
                Proj: {userTotals.projected.toFixed(1)}
              </div>
            )}
            {showActual && (
              <div className={`text-xs font-medium ${
                (userTotals.actual - userTotals.projected) > 0 ? 'text-success-400' :
                (userTotals.actual - userTotals.projected) < 0 ? 'text-danger-400' : 'text-warning-400'
              }`}>
                {(userTotals.actual - userTotals.projected) > 0 ? '+' : ''}{(userTotals.actual - userTotals.projected).toFixed(1)}
              </div>
            )}
          </div>

          {/* VS and Status */}
          <div className="text-center px-4">
            <div className="text-xs text-dark-500 mb-1">VS</div>
            <div className={`text-sm font-medium ${
              showActual
                ? (actualDiff > 0 ? 'text-success-400' : actualDiff < 0 ? 'text-danger-400' : 'text-warning-400')
                : (projectedDiff > 0 ? 'text-success-400' : projectedDiff < 0 ? 'text-danger-400' : 'text-warning-400')
            }`}>
              {showActual ? (
                isCompletedMatchup
                  ? (actualDiff > 0 ? 'WON' : actualDiff < 0 ? 'LOST' : 'TIED')
                  : (actualDiff > 0 ? 'WINNING' : actualDiff < 0 ? 'BEHIND' : 'TIED')
              ) : (
                projectedDiff > 0 ? 'FAVORED' : projectedDiff < 0 ? 'UNDERDOG' : 'EVEN'
              )}
            </div>
            {showActual && (
              <div className={`text-xs font-medium ${
                actualDiff > 0 ? 'text-success-400' :
                actualDiff < 0 ? 'text-danger-400' : 'text-warning-400'
              }`}>
                {actualDiff > 0 ? '+' : ''}{actualDiff.toFixed(1)}
              </div>
            )}
          </div>

          {/* Opponent Score */}
          <div className="text-center flex-1">
            <div className="text-2xl font-bold text-white">
              {showActual ? opponentTotals.actual.toFixed(1) : opponentTotals.projected.toFixed(1)}
            </div>
            {showActual && (
              <div className="text-xs text-dark-400">
                Proj: {opponentTotals.projected.toFixed(1)}
              </div>
            )}
            {showActual && (
              <div className={`text-xs font-medium ${
                (opponentTotals.actual - opponentTotals.projected) > 0 ? 'text-success-400' :
                (opponentTotals.actual - opponentTotals.projected) < 0 ? 'text-danger-400' : 'text-warning-400'
              }`}>
                {(opponentTotals.actual - opponentTotals.projected) > 0 ? '+' : ''}{(opponentTotals.actual - opponentTotals.projected).toFixed(1)}
              </div>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
};