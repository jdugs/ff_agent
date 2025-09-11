import React from 'react';
import type { Player } from '@/lib/types';
import { Card } from '@/components/ui/Card';
import { PlayerCard } from '@/components/team/PlayerCard';

interface StartingLineupProps {
  players: Player[];
}

export const StartingLineup: React.FC<StartingLineupProps> = ({ players }) => {
  return (
    <Card>
      <div className="mb-4">
        <h2 className="text-xl font-semibold text-white">Starting Lineup</h2>
        <p className="text-sm text-dark-400">Click any player for detailed analysis</p>
      </div>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {players.map((player) => (
          <PlayerCard 
            key={player.sleeper_id} 
            player={player} 
            size="large"
            showRanking={true}
            showProjection={true}
          />
        ))}
      </div>
    </Card>
  );
};
