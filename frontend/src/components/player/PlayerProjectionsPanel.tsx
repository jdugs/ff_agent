import React from 'react';
import type { Player } from '@/lib/types';
import { Card } from '@/components/ui/Card';
import { formatPoints } from '@/lib/utils';

interface PlayerProjectionsPanelProps {
  player: Player;
}

export const PlayerProjectionsPanel: React.FC<PlayerProjectionsPanelProps> = ({ player }) => {
  const hasProjections = player.projections || player.latest_projection || player.projection_range;
  
  if (!hasProjections) {
    return (
      <div className="text-center py-12 text-dark-400">
        <p>No projections available for this player</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Consensus Projection */}
      {player.projections && (
        <Card className="bg-success-500/10 border-success-500/30">
          <div className="text-center">
            <div className="text-3xl font-bold text-success-400 mb-1">
              {formatPoints(player.projections.fantasy_points)} pts
            </div>
            <div className="text-sm text-dark-300">
              Consensus Projection
            </div>
            <div className="text-xs text-dark-400 mt-1">
              From {player.projections.meta.provider_count} provider(s)
            </div>
          </div>
        </Card>
      )}

      {/* Legacy Projection */}
      {!player.projections && player.latest_projection && (
        <Card className="bg-success-500/10 border-success-500/30">
          <div className="text-center">
            <div className="text-3xl font-bold text-success-400 mb-1">
              {formatPoints(player.latest_projection)} pts
            </div>
            <div className="text-sm text-dark-300">
              Latest Projection
            </div>
          </div>
        </Card>
      )}

      {/* Projection Range */}
      {player.projection_range && (
        <Card>
          <h3 className="text-lg font-semibold text-white mb-4">Projection Range</h3>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-xl font-bold text-danger-400">
                {formatPoints(player.projection_range.min)}
              </div>
              <div className="text-sm text-dark-400">Minimum</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-warning-400">
                {formatPoints(player.projection_range.avg)}
              </div>
              <div className="text-sm text-dark-400">Average</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-success-400">
                {formatPoints(player.projection_range.max)}
              </div>
              <div className="text-sm text-dark-400">Maximum</div>
            </div>
          </div>
        </Card>
      )}

      {/* Statistical Breakdown */}
      {player.projections && (
        <Card>
          <h3 className="text-lg font-semibold text-white mb-4">Statistical Breakdown</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Passing */}
            {(player.projections.passing.yards > 0 || player.projections.passing.touchdowns > 0) && (
              <div className="text-center p-3 bg-dark-700 rounded">
                <h4 className="text-sm font-medium text-primary-400 mb-2">Passing</h4>
                <div className="space-y-1 text-sm">
                  <div><span className="text-dark-400">Yards:</span> <span className="text-white">{player.projections.passing.yards}</span></div>
                  <div><span className="text-dark-400">TDs:</span> <span className="text-white">{player.projections.passing.touchdowns}</span></div>
                  <div><span className="text-dark-400">INTs:</span> <span className="text-white">{player.projections.passing.interceptions}</span></div>
                </div>
              </div>
            )}

            {/* Rushing */}
            {(player.projections.rushing.yards > 0 || player.projections.rushing.touchdowns > 0) && (
              <div className="text-center p-3 bg-dark-700 rounded">
                <h4 className="text-sm font-medium text-warning-400 mb-2">Rushing</h4>
                <div className="space-y-1 text-sm">
                  <div><span className="text-dark-400">Yards:</span> <span className="text-white">{player.projections.rushing.yards}</span></div>
                  <div><span className="text-dark-400">TDs:</span> <span className="text-white">{player.projections.rushing.touchdowns}</span></div>
                </div>
              </div>
            )}

            {/* Receiving */}
            {(player.projections.receiving.yards > 0 || player.projections.receiving.receptions > 0) && (
              <div className="text-center p-3 bg-dark-700 rounded">
                <h4 className="text-sm font-medium text-success-400 mb-2">Receiving</h4>
                <div className="space-y-1 text-sm">
                  <div><span className="text-dark-400">Rec:</span> <span className="text-white">{player.projections.receiving.receptions}</span></div>
                  <div><span className="text-dark-400">Yards:</span> <span className="text-white">{player.projections.receiving.yards}</span></div>
                  <div><span className="text-dark-400">TDs:</span> <span className="text-white">{player.projections.receiving.touchdowns}</span></div>
                </div>
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Legacy Statistical Breakdown for old data */}
      {!player.projections && (
        <Card>
          <h3 className="text-lg font-semibold text-white mb-4">Statistical Breakdown</h3>
          <div className="text-center py-8 text-dark-400">
            <p>Detailed stats coming soon...</p>
            <p className="text-sm mt-2">
              Will show rushing, receiving, passing stats based on position
            </p>
          </div>
        </Card>
      )}
    </div>
  );
};