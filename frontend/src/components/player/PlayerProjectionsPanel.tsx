import React from 'react';
import type { Player } from '@/lib/types';
import { Card } from '@/components/ui/Card';
import { formatPoints } from '@/lib/utils';

interface PlayerProjectionsPanelProps {
  player: Player;
}

export const PlayerProjectionsPanel: React.FC<PlayerProjectionsPanelProps> = ({ player }) => {
  if (!player.latest_projection && !player.projection_range) {
    return (
      <div className="text-center py-12 text-dark-400">
        <p>No projections available for this player</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Current Projection */}
      {player.latest_projection && (
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
      <Card>
        <h3 className="text-lg font-semibold text-white mb-4">Statistical Breakdown</h3>
        <div className="text-center py-8 text-dark-400">
          <p>Detailed stats coming soon...</p>
          <p className="text-sm mt-2">
            Will show rushing, receiving, passing stats based on position
          </p>
        </div>
      </Card>
    </div>
  );
};