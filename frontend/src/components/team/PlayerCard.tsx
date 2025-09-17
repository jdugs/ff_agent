'use client';

import React from 'react';
import type { Player } from '@/lib/types';
import { useUIStore } from '@/store/uiStore';
import { Badge } from '@/components/ui/Badge';
import { formatPoints } from '@/lib/utils';
import { cn } from '@/lib/utils';

interface PlayerCardProps {
  player: Player;
  rosterSlot?: string;
  className?: string;
  reversed?: boolean;
}

export const PlayerCard: React.FC<PlayerCardProps> = ({
  player,
  rosterSlot,
  className,
  reversed = false,
}) => {
  const { openPlayerModal } = useUIStore();

  const handleClick = () => {
    openPlayerModal(player);
  };

  // Calculate difference between actual and projected
  // Use ppr field which contains our league-specific scoring calculation
  const actualPoints = player.actual_stats?.fantasy_points.ppr ?? 0;
  const projectedPoints = player.projections?.fantasy_points ?? 0;
  const difference = actualPoints - projectedPoints;
  const hasActual = player.actual_stats !== null && player.actual_stats !== undefined;

  // Get opponent matchup info from player data
  const opponent = player.opponent || "vs ???";
  const gameTime = player.game_time || "TBD";

  return (
    <div
      className={cn(
        'flex items-center justify-between p-2 bg-dark-800 hover:bg-dark-700 rounded cursor-pointer transition-colors',
        reversed && 'flex-row-reverse',
        className
      )}
      onClick={handleClick}
    >
      {/* Left side - Position slot and player info (or right side when reversed) */}
      <div className={cn(
        'flex items-center flex-1 min-w-0',
        reversed ? 'space-x-reverse space-x-2 flex-row-reverse' : 'space-x-2'
      )}>
        {/* Roster slot badge */}
        {rosterSlot && (
          <Badge
            variant="info"
            size="sm"
            className="text-dark-400 bg-dark-700 min-w-8 text-center text-xs px-1"
          >
            {rosterSlot}
          </Badge>
        )}

        {/* Player info */}
        <div className="flex-1 min-w-0">
          <div className={cn(
            'flex items-center',
            reversed ? 'space-x-reverse space-x-1 flex-row-reverse justify-end' : 'space-x-1'
          )}>
            <Badge
              size="sm"
              className={cn(
                'text-white text-xs px-1',
                player.position === 'QB' ? 'bg-red-600' :
                player.position === 'RB' ? 'bg-blue-600' :
                player.position === 'WR' ? 'bg-green-600' :
                player.position === 'TE' ? 'bg-yellow-600' :
                player.position === 'K' ? 'bg-purple-600' :
                player.position === 'DEF' ? 'bg-gray-600' : 'bg-dark-600'
              )}
            >
              {player.position}
            </Badge>
            <span className="text-xs text-dark-400">{player.team}</span>
          </div>
          <h3 className={cn(
            'font-medium text-white text-xs truncate leading-tight',
            reversed && 'text-right'
          )}>
            {player.player_name}
          </h3>
          <div className={cn(
            'text-xs text-dark-500 leading-tight',
            reversed && 'text-right'
          )}>
            {opponent} • {gameTime}
          </div>
        </div>
      </div>

      {/* Right side - Fantasy points (or left side when reversed) */}
      <div className={cn(
        'flex items-center text-xs',
        reversed ? 'space-x-reverse space-x-2 flex-row-reverse' : 'space-x-2'
      )}>
        {/* Projected */}
        <div className="text-center min-w-8">
          <div className="text-success-400 font-medium">
            {formatPoints(projectedPoints)}
          </div>
        </div>

        {/* Actual */}
        <div className="text-center min-w-8">
          <div className={cn(
            "font-medium",
            hasActual ? "text-primary-400" : "text-dark-600"
          )}>
            {hasActual ? formatPoints(actualPoints) : "-"}
          </div>
        </div>

        {/* Difference */}
        <div className="text-center min-w-8">
          <div className={cn(
            "font-medium",
            !hasActual ? "text-dark-600" :
            difference > 0 ? "text-success-400" :
            difference < 0 ? "text-danger-400" : "text-warning-400"
          )}>
            {!hasActual ? "-" :
             difference > 0 ? `+${formatPoints(difference)}` :
             formatPoints(difference)}
          </div>
        </div>
      </div>
    </div>
  );
};