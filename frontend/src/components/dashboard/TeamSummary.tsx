'use client';

import React from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { formatPoints } from '@/lib/utils';
import type { TeamDashboard } from '@/lib/types';

interface TeamSummaryProps {
  team: TeamDashboard;
}

export const TeamSummary: React.FC<TeamSummaryProps> = ({ team }) => {
  const { roster_summary, lineup } = team.data;
  
  // Calculate key stats
  const totalProjected = lineup.starters.reduce((sum, player) => 
    sum + (player.projections?.fantasy_points || 0), 0
  );
  
  const totalActual = lineup.starters.reduce((sum, player) => 
    sum + (player.actual_stats?.fantasy_points.ppr || 0), 0
  );

  const playersWithStats = lineup.starters.filter(p => p.actual_stats).length;
  const topProjection = Math.max(...lineup.starters.map(p => p.projections?.fantasy_points || 0));
  const topActual = Math.max(...lineup.starters.map(p => p.actual_stats?.fantasy_points.ppr || 0));

  return (
    <Card>
      <div className="space-y-6">
        {/* Header with Record and Points */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-white mb-1">Your Team</h2>
            <div className="flex items-center space-x-4 text-sm">
              <Badge variant="info" size="sm">
                {roster_summary.team_record.wins}-{roster_summary.team_record.losses}-{roster_summary.team_record.ties}
              </Badge>
              <span className="text-dark-400">
                {formatPoints(roster_summary.team_record.points_for)} PF
              </span>
              <span className="text-dark-400">
                {formatPoints(roster_summary.team_record.points_against)} PA
              </span>
            </div>
          </div>
          
          {/* Week Status */}
          <div className="text-right">
            <div className="text-sm text-dark-400">This Week</div>
            <div className="flex items-center space-x-2">
              {playersWithStats > 0 && (
                <span className="text-primary-400 font-medium">
                  {formatPoints(totalActual)} actual
                </span>
              )}
              <span className="text-success-400 font-medium">
                {formatPoints(totalProjected)} proj
              </span>
            </div>
          </div>
        </div>

        {/* Key Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {/* Roster Composition */}
          <div className="text-center p-3 bg-dark-800 rounded">
            <div className="text-lg font-bold text-white">{roster_summary.starters_count}</div>
            <div className="text-xs text-dark-400">Starters</div>
          </div>
          
          {/* Bench Depth */}
          <div className="text-center p-3 bg-dark-800 rounded">
            <div className="text-lg font-bold text-white">{roster_summary.bench_count}</div>
            <div className="text-xs text-dark-400">Bench</div>
          </div>
          
          {/* Top Projection */}
          <div className="text-center p-3 bg-dark-800 rounded">
            <div className="text-lg font-bold text-success-400">{formatPoints(topProjection)}</div>
            <div className="text-xs text-dark-400">Top Proj</div>
          </div>
          
          {/* Performance Status */}
          <div className="text-center p-3 bg-dark-800 rounded">
            <div className="text-lg font-bold text-primary-400">
              {playersWithStats > 0 ? formatPoints(topActual) : '-'}
            </div>
            <div className="text-xs text-dark-400">Top Actual</div>
          </div>
        </div>

        {/* Starting Lineup Summary */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-semibold text-white">Starting Lineup</h3>
            <div className="text-sm text-dark-400">
              {playersWithStats}/{roster_summary.starters_count} played
            </div>
          </div>
          
          {/* Compact player list */}
          <div className="space-y-1">
            {lineup.starters.map((player) => {
              const hasPlayed = player.actual_stats !== null;
              const projected = player.projections?.fantasy_points || 0;
              const actual = player.actual_stats?.fantasy_points.ppr || 0;
              const diff = actual - projected;

              return (
                <div key={player.sleeper_id} className="flex items-center justify-between p-2 bg-dark-800 rounded text-sm">
                  <div className="flex items-center space-x-2 flex-1 min-w-0">
                    <Badge 
                      size="sm"
                      className={`text-white text-xs px-1 ${
                        player.position === 'QB' ? 'bg-red-600' :
                        player.position === 'RB' ? 'bg-blue-600' :
                        player.position === 'WR' ? 'bg-green-600' :
                        player.position === 'TE' ? 'bg-yellow-600' :
                        player.position === 'K' ? 'bg-purple-600' :
                        player.position === 'DEF' ? 'bg-gray-600' : 'bg-dark-600'
                      }`}
                    >
                      {player.position}
                    </Badge>
                    <span className="text-white font-medium truncate">
                      {player.player_name}
                    </span>
                    <span className="text-dark-400 text-xs">{player.team}</span>
                  </div>
                  
                  <div className="flex items-center space-x-3 text-xs">
                    <span className="text-success-400">{formatPoints(projected)}</span>
                    <span className={hasPlayed ? "text-primary-400" : "text-dark-600"}>
                      {hasPlayed ? formatPoints(actual) : '-'}
                    </span>
                    <span className={`min-w-12 text-right ${
                      !hasPlayed ? 'text-dark-600' :
                      diff > 0 ? 'text-success-400' :
                      diff < 0 ? 'text-danger-400' : 'text-warning-400'
                    }`}>
                      {!hasPlayed ? '-' : 
                       diff > 0 ? `+${formatPoints(diff)}` :
                       formatPoints(diff)}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </Card>
  );
};