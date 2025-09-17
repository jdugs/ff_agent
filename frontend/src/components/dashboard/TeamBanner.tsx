'use client';

import React from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { formatPoints } from '@/lib/utils';
import type { TeamDashboard } from '@/lib/types';

interface TeamBannerProps {
  team: TeamDashboard;
}

export const TeamBanner: React.FC<TeamBannerProps> = ({ team }) => {
  const { roster_summary, lineup } = team.data;
  
  // Calculate key stats
  const totalProjected = lineup.starters.reduce((sum, player) => 
    sum + (player.projections?.fantasy_points || 0), 0
  );
  
  const totalActual = lineup.starters.reduce((sum, player) => 
    sum + (player.actual_stats?.fantasy_points.ppr || 0), 0
  );

  const playersWithStats = lineup.starters.filter(p => p.actual_stats).length;
  const projectionDiff = totalActual - totalProjected;

  return (
    <Card className="bg-gradient-to-r from-dark-800 to-dark-700">
      <div className="flex items-center justify-between">
        {/* Left: Team Info */}
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Your Team</h1>
          <div className="flex items-center space-x-6 text-sm">
            <Badge variant="info" size="sm" className="text-lg px-3 py-1">
              {roster_summary.team_record.wins}-{roster_summary.team_record.losses}-{roster_summary.team_record.ties}
            </Badge>
            <div className="flex items-center space-x-4 text-dark-300">
              <span>
                <span className="text-dark-400">PF:</span> {formatPoints(roster_summary.team_record.points_for)}
              </span>
              <span>
                <span className="text-dark-400">PA:</span> {formatPoints(roster_summary.team_record.points_against)}
              </span>
              <span>
                <span className="text-dark-400">Players:</span> {playersWithStats}/{roster_summary.starters_count} played
              </span>
            </div>
          </div>
        </div>

        {/* Right: This Week Performance */}
        <div className="text-right">
          <div className="text-sm text-dark-400 mb-1">This Week</div>
          <div className="flex items-center space-x-4">
            {/* Projected */}
            <div className="text-center">
              <div className="text-2xl font-bold text-success-400">
                {formatPoints(totalProjected)}
              </div>
              <div className="text-xs text-dark-400">Projected</div>
            </div>

            {/* Actual (if any games played) */}
            {playersWithStats > 0 && (
              <>
                <div className="text-dark-500">→</div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-primary-400">
                    {formatPoints(totalActual)}
                  </div>
                  <div className="text-xs text-dark-400">Actual</div>
                </div>

                {/* Difference */}
                <div className="text-center">
                  <div className={`text-xl font-bold ${
                    projectionDiff > 0 ? 'text-success-400' :
                    projectionDiff < 0 ? 'text-danger-400' : 'text-warning-400'
                  }`}>
                    {projectionDiff > 0 ? '+' : ''}{formatPoints(projectionDiff)}
                  </div>
                  <div className="text-xs text-dark-400">vs Proj</div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
};