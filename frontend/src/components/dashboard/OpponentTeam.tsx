'use client';

import React, { useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { PlayerCard } from '@/components/team/PlayerCard';
import { useTeamStore } from '@/store/teamStore';
import { ApiClient } from '@/lib/api';
import type { Matchup, MatchupPlayer } from '@/lib/types';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

export const OpponentTeam: React.FC = () => {
  const { selectedLeagueId, selectedUserId, currentWeek } = useTeamStore();
  const [matchup, setMatchup] = useState<Matchup | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [rosterPositions, setRosterPositions] = useState<string[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      if (!selectedLeagueId || !selectedUserId || !currentWeek) return;

      setLoading(true);
      setError(null);

      try {
        // Fetch matchup data and roster positions in parallel
        const [matchupData, leagueResponse] = await Promise.all([
          ApiClient.getMyMatchup(selectedLeagueId, currentWeek, selectedUserId),
          fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/sleeper/league/${selectedLeagueId}`)
            .then(res => res.json())
        ]);

        setMatchup(matchupData);
        if (leagueResponse.roster_positions) {
          setRosterPositions(leagueResponse.roster_positions);
        }
      } catch (err) {
        console.error('Failed to load opponent data:', err);
        setError('Failed to load opponent data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [selectedLeagueId, selectedUserId, currentWeek]);

  // Convert MatchupPlayer to Player type for PlayerCard
  const convertMatchupPlayerToPlayer = (matchupPlayer: MatchupPlayer, slot: string) => ({
    sleeper_id: matchupPlayer.sleeper_id,
    player_name: matchupPlayer.player_name || 'Unknown Player',
    position: matchupPlayer.position || 'UNKNOWN',
    team: matchupPlayer.team || '',
    is_starter: slot !== 'BN',
    opponent: matchupPlayer.opponent || "vs ???",
    game_time: matchupPlayer.game_time || "TBD",
    projections: matchupPlayer.projections ? {
      fantasy_points: matchupPlayer.projections.fantasy_points,
      passing: { yards: 0, touchdowns: 0, interceptions: 0 },
      rushing: { yards: 0, touchdowns: 0 },
      receiving: { yards: 0, touchdowns: 0, receptions: 0 },
      meta: { provider_count: 1, confidence_score: 1, last_updated: new Date().toISOString() }
    } : null,
    actual_stats: null // Opponents don't need actual stats for this view
  });

  // Organize opponent players by roster positions
  const organizeOpponentBySlots = () => {
    if (!matchup?.opponent_roster?.players || !rosterPositions.length) {
      return matchup?.opponent_roster?.players.map(player => ({ 
        player: convertMatchupPlayerToPlayer(player, player.position || 'UNKNOWN'), 
        slot: player.position || 'UNKNOWN' 
      })) || [];
    }

    const availablePlayers = [...matchup.opponent_roster.players];
    const organizedPlayers: { player: any; slot: string }[] = [];

    // Assign players to starting lineup slots
    rosterPositions.forEach(slot => {
      if (slot === 'BN') return; // Skip bench for now

      let assignedPlayer: MatchupPlayer | null = null;

      if (slot === 'FLEX') {
        assignedPlayer = availablePlayers.find(p => ['RB', 'WR', 'TE'].includes(p.position || '')) || null;
      } else if (slot === 'SUPER_FLEX') {
        assignedPlayer = availablePlayers.find(p => ['QB', 'RB', 'WR', 'TE'].includes(p.position || '')) || null;
      } else {
        assignedPlayer = availablePlayers.find(p => p.position === slot) || null;
      }

      if (assignedPlayer) {
        organizedPlayers.push({ 
          player: convertMatchupPlayerToPlayer(assignedPlayer, slot), 
          slot 
        });
        const index = availablePlayers.indexOf(assignedPlayer);
        availablePlayers.splice(index, 1);
      } else {
        // Empty slot
        organizedPlayers.push({ 
          player: {
            sleeper_id: `opp-empty-${slot}`,
            player_name: 'Empty Slot',
            position: slot,
            team: '',
            is_starter: true,
            projections: null,
            actual_stats: null
          },
          slot 
        });
      }
    });

    return organizedPlayers;
  };

  if (loading) {
    return (
      <Card>
        <div className="flex items-center justify-center py-8">
          <LoadingSpinner size="md" />
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <div className="text-center py-8 text-danger-400">
          <p>{error}</p>
        </div>
      </Card>
    );
  }

  if (!matchup?.opponent_roster) {
    return (
      <Card>
        <h2 className="text-xl font-bold text-white mb-4">Opponent</h2>
        <div className="text-center py-8 text-dark-400">
          <p className="text-lg">🏖️ Bye Week</p>
          <p className="text-sm">No opponent this week</p>
        </div>
      </Card>
    );
  }

  const organizedPlayers = organizeOpponentBySlots();
  
  // Calculate totals for opponent starting lineup (exclude empty slots)
  const validPlayers = organizedPlayers.filter(({ player }) => player.sleeper_id && !player.sleeper_id.startsWith('opp-empty'));
  const totalProjected = validPlayers.reduce((sum, { player }) => 
    sum + (player.projections?.fantasy_points ?? 0), 0);
  const totalActual = validPlayers.reduce((sum, { player }) => 
    sum + (player.actual_stats?.fantasy_points?.half_ppr ?? 0), 0);
  const hasActualData = validPlayers.some(({ player }) => player.actual_stats !== null);

  return (
    <Card>
      <h2 className="text-xl font-bold text-white mb-4">
        Opponent ({matchup.opponent_roster.record})
      </h2>
      <div className="space-y-1">
        {organizedPlayers.map(({ player, slot }, index) => (
          <PlayerCard
            key={`opp-${player.sleeper_id}-${index}`}
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
  );
};