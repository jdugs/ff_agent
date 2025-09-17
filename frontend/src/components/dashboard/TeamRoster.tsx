'use client';

import React, { useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { PlayerCard } from '@/components/team/PlayerCard';
import { useTeamStore } from '@/store/teamStore';
import type { Player } from '@/lib/types';

interface TeamRosterProps {
  players: Player[];
}

export const TeamRoster: React.FC<TeamRosterProps> = ({ players }) => {
  const { selectedLeagueId } = useTeamStore();
  const [rosterPositions, setRosterPositions] = useState<string[]>([]);

  useEffect(() => {
    const fetchRosterPositions = async () => {
      if (selectedLeagueId) {
        try {
          const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/sleeper/league/${selectedLeagueId}`);
          const leagueData = await response.json();
          if (leagueData.roster_positions) {
            setRosterPositions(leagueData.roster_positions);
          }
        } catch (error) {
          console.error('Failed to fetch roster positions:', error);
        }
      }
    };

    fetchRosterPositions();
  }, [selectedLeagueId]);

  // Organize players by position based on roster_positions order
  const organizePlayersByRosterSlots = () => {
    if (!rosterPositions.length) {
      return players.map(player => ({ player, slot: player.position }));
    }

    const starters = players.filter(p => p.is_starter);
    const bench = players.filter(p => !p.is_starter);
    
    const availablePlayers = [...starters];
    const organizedPlayers: { player: Player; slot: string }[] = [];

    // Assign players to starting lineup slots
    rosterPositions.forEach(slot => {
      if (slot === 'BN') return; // Skip bench slots

      let assignedPlayer: Player | null = null;

      if (slot === 'FLEX') {
        assignedPlayer = availablePlayers.find(p => ['RB', 'WR', 'TE'].includes(p.position)) || null;
      } else if (slot === 'SUPER_FLEX') {
        assignedPlayer = availablePlayers.find(p => ['QB', 'RB', 'WR', 'TE'].includes(p.position)) || null;
      } else {
        assignedPlayer = availablePlayers.find(p => p.position === slot) || null;
      }

      if (assignedPlayer) {
        organizedPlayers.push({ player: assignedPlayer, slot });
        const index = availablePlayers.indexOf(assignedPlayer);
        availablePlayers.splice(index, 1);
      }
    });

    // Add remaining starters and bench
    availablePlayers.forEach(player => {
      organizedPlayers.push({ player, slot: player.position });
    });
    bench.forEach(player => {
      organizedPlayers.push({ player, slot: 'BN' });
    });

    return organizedPlayers;
  };

  if (!players?.length) {
    return (
      <Card>
        <h2 className="text-xl font-bold text-white mb-4">Your Lineup</h2>
        <div className="text-center py-8 text-dark-400">
          <p>No lineup available</p>
        </div>
      </Card>
    );
  }

  const organizedPlayers = organizePlayersByRosterSlots();
  const startingPlayers = organizedPlayers.filter(({ slot }) => slot !== 'BN');
  const benchPlayers = organizedPlayers.filter(({ slot }) => slot === 'BN');

  // Calculate totals for starting lineup
  const totalProjected = startingPlayers.reduce((sum, { player }) => 
    sum + (player.projections?.fantasy_points ?? 0), 0);
  const totalActual = startingPlayers.reduce((sum, { player }) =>
    sum + (player.actual_stats?.fantasy_points.ppr ?? 0), 0);
  const hasActualData = startingPlayers.some(({ player }) => player.actual_stats !== null);

  return (
    <div className="space-y-4">
      {/* Starting Lineup */}
      <Card>
        <h2 className="text-lg font-bold text-white mb-3">Starting Lineup</h2>
        <div className="space-y-1">
          {startingPlayers.map(({ player, slot }, index) => (
            <PlayerCard
              key={`${player.sleeper_id}-${index}`}
              player={player}
              rosterSlot={slot}
            />
          ))}
        </div>
        {/* Totals */}
        <div className="mt-4 pt-4 border-t border-dark-700">
          <div className="flex justify-between items-center text-sm">
            <span className="text-dark-400">Total:</span>
            <div className="flex items-center space-x-4">
              <div className="text-center">
                <div className="text-success-400 font-medium">
                  {totalProjected.toFixed(1)}
                </div>
                <div className="text-xs text-dark-500">Proj</div>
              </div>
              {hasActualData && (
                <div className="text-center">
                  <div className="text-primary-400 font-medium">
                    {totalActual.toFixed(1)}
                  </div>
                  <div className="text-xs text-dark-500">Actual</div>
                </div>
              )}
              {hasActualData && (
                <div className="text-center">
                  <div className={`font-medium ${
                    totalActual > totalProjected ? 'text-success-400' : 
                    totalActual < totalProjected ? 'text-danger-400' : 'text-warning-400'
                  }`}>
                    {totalActual > totalProjected ? '+' : ''}{(totalActual - totalProjected).toFixed(1)}
                  </div>
                  <div className="text-xs text-dark-500">Diff</div>
                </div>
              )}
            </div>
          </div>
        </div>
      </Card>

      {/* Bench */}
      {benchPlayers.length > 0 && (
        <Card>
          <h2 className="text-lg font-bold text-white mb-3">Bench</h2>
          <div className="space-y-1">
            {benchPlayers.map(({ player, slot }, index) => (
              <PlayerCard
                key={`${player.sleeper_id}-bench-${index}`}
                player={player}
                rosterSlot={slot}
              />
            ))}
          </div>
        </Card>
      )}
    </div>
  );
};