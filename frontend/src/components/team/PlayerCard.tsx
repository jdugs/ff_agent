'use client';

import React from 'react';
import type { Player } from '@/lib/types';
import { useUIStore } from '@/store/uiStore';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Tooltip } from '@/components/ui/Tooltip';
import { 
  getPositionColor, 
  getStatusColor, 
  getStatusIcon, 
  formatPoints,
  getTrendIcon 
} from '@/lib/utils';
import { cn } from '@/lib/utils';

interface PlayerCardProps {
  player: Player;
  size?: 'small' | 'medium' | 'large';
  showRanking?: boolean;
  showProjection?: boolean;
  className?: string;
}

export const PlayerCard: React.FC<PlayerCardProps> = ({
  player,
  size = 'medium',
  showRanking = true,
  showProjection = true,
  className,
}) => {
  const { openPlayerModal } = useUIStore();

  const handleClick = () => {
    openPlayerModal(player);
  };

  const sizeClasses = {
    small: 'p-3',
    medium: 'p-4',
    large: 'p-4',
  };

  const statusColor = getStatusColor(player.start_sit_recommendation, player.red_flags);
  const statusIcon = getStatusIcon(player.start_sit_recommendation, player.red_flags);
  const positionColor = getPositionColor(player.position);

  return (
    <Card 
      className={cn(
        'cursor-pointer hover:scale-105 transition-all duration-200 border-2',
        statusColor,
        sizeClasses[size],
        className
      )}
      padding="none"
      onClick={handleClick}
    >
      <div className="space-y-3">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-2 mb-1">
              <Badge className={positionColor} size="sm">
                {player.position}
              </Badge>
              <span className="text-xs text-dark-400">{player.team}</span>
              {player.red_flags.length > 0 && (
                <Tooltip content={player.red_flags.join(', ')}>
                  <span className="text-danger-400">⚠️</span>
                </Tooltip>
              )}
            </div>
            <h3 className="font-semibold text-white text-sm truncate">
              {player.name}
            </h3>
            {player.injury_status && (
              <p className="text-xs text-danger-400">
                {player.injury_status}
              </p>
            )}
          </div>
          <div className="flex flex-col items-end space-y-1">
            <span className="text-lg">{statusIcon}</span>
            {player.rank_trend && (
              <span className="text-xs">
                {getTrendIcon(player.rank_trend)}
              </span>
            )}
          </div>
        </div>

        {/* Rankings */}
        {showRanking && (
          <div className="space-y-2">
            {player.consensus_rank && (
              <div className="flex items-center justify-between">
                <span className="text-xs text-dark-400">Consensus Rank:</span>
                <span className="text-sm font-medium text-white">
                  #{Math.round(player.consensus_rank)}
                </span>
              </div>
            )}
            
            {player.rankings.length > 0 && (
              <div className="flex items-center space-x-2">
                {player.rankings.slice(0, 3).map((ranking, index) => (
                  <Tooltip 
                    key={index}
                    content={`${ranking.source_name}: #${ranking.position_rank}`}
                  >
                    <div className="text-xs bg-dark-700 px-2 py-1 rounded">
                      #{ranking.position_rank}
                    </div>
                  </Tooltip>
                ))}
                {player.rankings.length > 3 && (
                  <span className="text-xs text-dark-400">
                    +{player.rankings.length - 3} more
                  </span>
                )}
              </div>
            )}
          </div>
        )}

        {/* Projection */}
        {showProjection && player.latest_projection && (
          <div className="flex items-center justify-between pt-2 border-t border-dark-700">
            <span className="text-xs text-dark-400">Projected:</span>
            <span className="text-sm font-medium text-success-400">
              {formatPoints(player.latest_projection)} pts
            </span>
          </div>
        )}

        {/* Confidence Score */}
        {player.confidence_score && (
          <div className="flex items-center justify-between">
            <span className="text-xs text-dark-400">Confidence:</span>
            <div className="flex items-center space-x-1">
              <div className="w-16 bg-dark-700 rounded-full h-1.5">
                <div 
                  className={cn(
                    'h-1.5 rounded-full transition-all',
                    player.confidence_score > 0.8 ? 'bg-success-500' :
                    player.confidence_score > 0.6 ? 'bg-warning-500' : 'bg-danger-500'
                  )}
                  style={{ width: `${player.confidence_score * 100}%` }}
                />
              </div>
              <span className="text-xs text-white">
                {Math.round(player.confidence_score * 100)}%
              </span>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};