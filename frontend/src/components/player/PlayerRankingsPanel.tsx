import React from 'react';
import type { Player } from '@/lib/types';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { formatTimeAgo } from '@/lib/utils';

interface PlayerRankingsPanelProps {
  player: Player;
}

export const PlayerRankingsPanel: React.FC<PlayerRankingsPanelProps> = ({ player }) => {
  const rankings = player.rankings || [];
  
  if (rankings.length === 0) {
    return (
      <div className="text-center py-12 text-dark-400">
        <p>No rankings available for this player</p>
        {player.projections && (
          <div className="mt-4">
            <p className="text-sm text-dark-300">But we have consensus projections!</p>
            <div className="mt-2 text-lg font-bold text-success-400">
              {player.projections.fantasy_points.toFixed(2)} projected points
            </div>
            <p className="text-xs text-dark-400">
              From {player.projections.meta.provider_count} provider(s)
            </p>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Consensus Summary */}
      {player.consensus_rank && (
        <Card className="bg-primary-500/10 border-primary-500/30">
          <div className="text-center">
            <div className="text-3xl font-bold text-primary-400 mb-1">
              #{Math.round(player.consensus_rank)}
            </div>
            <div className="text-sm text-dark-300">
              Consensus Position Rank
            </div>
            <div className="text-xs text-dark-400 mt-1">
              Based on {rankings.length} sources
            </div>
          </div>
        </Card>
      )}

      {/* Individual Rankings */}
      <div className="space-y-3">
        <h3 className="text-lg font-semibold text-white">Source Rankings</h3>
        {rankings.map((ranking, index) => (
          <Card key={index} className="bg-dark-700">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-medium text-white">
                  {ranking.source_name}
                </h4>
                <p className="text-sm text-dark-400">
                  Updated {formatTimeAgo(ranking.timestamp)}
                </p>
              </div>
              
              <div className="flex items-center space-x-4">
                {ranking.tier && (
                  <div className="text-center">
                    <div className="text-sm font-medium text-warning-400">
                      Tier {ranking.tier}
                    </div>
                  </div>
                )}
                
                <div className="text-center">
                  <div className="text-lg font-bold text-white">
                    #{ranking.position_rank}
                  </div>
                  <div className="text-xs text-dark-400">Position</div>
                </div>
                
                {ranking.overall_rank && (
                  <div className="text-center">
                    <div className="text-lg font-bold text-dark-300">
                      #{ranking.overall_rank}
                    </div>
                    <div className="text-xs text-dark-400">Overall</div>
                  </div>
                )}
                
                {ranking.projection && (
                  <div className="text-center">
                    <div className="text-lg font-bold text-success-400">
                      {ranking.projection.toFixed(2)}
                    </div>
                    <div className="text-xs text-dark-400">Projected</div>
                  </div>
                )}
                
                <Badge variant={
                  ranking.confidence === 'high' ? 'success' :
                  ranking.confidence === 'medium' ? 'warning' : 'danger'
                }>
                  {ranking.confidence}
                </Badge>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};