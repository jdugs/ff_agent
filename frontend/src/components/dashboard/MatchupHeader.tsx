'use client';

import React from 'react';
import { Card } from '@/components/ui/Card';
import { useTeamStore } from '@/store/teamStore';
import type { Player } from '@/lib/types';

interface MatchupHeaderProps {
  userPlayers?: Player[];
  opponentPlayers?: Player[];
  isByeWeek?: boolean;
}

export const MatchupHeader: React.FC<MatchupHeaderProps> = ({
  userPlayers,
  opponentPlayers,
  isByeWeek = false
}) => {
  const { currentWeek } = useTeamStore();

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

  return (
    <Card>
      <div className="text-center py-4">
        <h2 className="text-lg font-bold text-white mb-4">Week {currentWeek} Matchup</h2>

        {/* Team Names */}
        <div className="flex justify-between items-center mb-4">
          <div className="text-left">
            <h3 className="font-semibold text-white">Your Team</h3>
          </div>
          <div className="text-xs text-dark-400 px-2">VS</div>
          <div className="text-right">
            <h3 className="font-semibold text-white">
              Opponent
            </h3>
          </div>
        </div>

        {/* Projected Totals */}
        <div className="flex justify-between items-center mb-2">
          <div className="text-center">
            <div className="text-xl font-bold text-success-400">
              {userTotals.projected.toFixed(2)}
            </div>
          </div>
          <div className="text-center px-4">
            <div className="text-xs text-dark-500 mb-1">Projected</div>
            <div className={`text-sm font-medium ${
              projectedDiff > 0 ? 'text-success-400' :
              projectedDiff < 0 ? 'text-danger-400' : 'text-warning-400'
            }`}>
              {projectedDiff > 0 ? '+' : ''}{projectedDiff.toFixed(2)}
            </div>
          </div>
          <div className="text-center">
            <div className="text-xl font-bold text-success-400">
              {opponentTotals.projected.toFixed(2)}
            </div>
          </div>
        </div>

        {/* Actual Totals (if available) */}
        {showActual && (
          <div className="flex justify-between items-center border-t border-dark-700 pt-2">
            <div className="text-center">
              <div className="text-xl font-bold text-primary-400">
                {userTotals.actual.toFixed(2)}
              </div>
            </div>
            <div className="text-center px-4">
              <div className="text-xs text-dark-500 mb-1">Actual</div>
              <div className={`text-sm font-medium ${
                actualDiff > 0 ? 'text-success-400' :
                actualDiff < 0 ? 'text-danger-400' : 'text-warning-400'
              }`}>
                {actualDiff > 0 ? '+' : ''}{actualDiff.toFixed(2)}
              </div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-primary-400">
                {opponentTotals.actual.toFixed(2)}
              </div>
            </div>
          </div>
        )}

        {/* Win Probability or Status */}
        <div className="mt-3 pt-2 border-t border-dark-700">
          {showActual ? (
            <div className={`text-sm font-medium ${
              actualDiff > 0 ? 'text-success-400' :
              actualDiff < 0 ? 'text-danger-400' : 'text-warning-400'
            }`}>
              {actualDiff > 0 ? '🎉 You are winning!' :
               actualDiff < 0 ? '📉 You are behind' : '🤝 It\'s tied!'}
            </div>
          ) : (
            <div className={`text-sm font-medium ${
              projectedDiff > 0 ? 'text-success-400' :
              projectedDiff < 0 ? 'text-danger-400' : 'text-warning-400'
            }`}>
              {projectedDiff > 0 ? '📈 Projected to win' :
               projectedDiff < 0 ? '⚠️ Projected to lose' : '🤞 Projected tie'}
            </div>
          )}
        </div>
      </div>
    </Card>
  );
};