'use client';

import React, { useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { PlayerCard } from '@/components/team/PlayerCard';
import { useTeamStore } from '@/store/teamStore';
import { ApiClient } from '@/lib/api';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import type { Player, Matchup, MatchupPlayer } from '@/lib/types';

interface MatchupTeamProps {
  teamType: 'user' | 'opponent';
  players?: Player[]; // For user team, players come from props
  isFlipped?: boolean; // For visual symmetry
  showTitle?: boolean;
  teamRecord?: string; // Optional team record to display
}

export const MatchupTeam: React.FC<MatchupTeamProps> = ({
  teamType,
  players,
  isFlipped = false,
  showTitle = true,
  teamRecord
}) => {
  const { selectedLeagueId, selectedUserId, currentWeek } = useTeamStore();
  const [matchup, setMatchup] = useState<Matchup | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [rosterPositions, setRosterPositions] = useState<string[]>([]);

  // For opponent team, we need to fetch matchup data (only if no players provided)
  useEffect(() => {
    if (teamType === 'opponent' && !players?.length) {
      const fetchOpponentData = async () => {
        if (!selectedLeagueId || !selectedUserId || !currentWeek) return;

        setLoading(true);
        setError(null);

        try {
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

      fetchOpponentData();
    }
  }, [teamType, selectedLeagueId, selectedUserId, currentWeek, players]);

  // Fetch roster positions for user team
  useEffect(() => {
    if (teamType === 'user') {
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
    }
  }, [teamType, selectedLeagueId]);

  // Convert MatchupPlayer to Player type for opponent team
  const convertMatchupPlayerToPlayer = (matchupPlayer: MatchupPlayer, slot: string): Player => ({
    sleeper_id: matchupPlayer.sleeper_id,
    player_name: matchupPlayer.player_name || 'Unknown Player',
    position: matchupPlayer.position || 'UNKNOWN',
    team: matchupPlayer.team || '',
    is_starter: slot !== 'BN',
    opponent: matchupPlayer.opponent || "vs ???",
    game_time: matchupPlayer.game_time || "TBD",
    player_details: {
      age: null,
      height: null,
      weight: null,
      college: null,
      years_exp: null,
      status: 'Active',
      fantasy_positions: [matchupPlayer.position || 'UNKNOWN']
    },
    external_ids: {
      espn_id: null,
      rotowire_id: null,
      fantasy_data_id: null,
      yahoo_id: null,
      stats_id: null
    },
    projections: matchupPlayer.projections ? {
      fantasy_points: matchupPlayer.projections.fantasy_points,
      passing: { yards: 0, touchdowns: 0, interceptions: 0 },
      rushing: { yards: 0, touchdowns: 0 },
      receiving: { yards: 0, touchdowns: 0, receptions: 0 },
      meta: { provider_count: 1, confidence_score: 1, last_updated: new Date().toISOString() }
    } : null,
    actual_stats: matchupPlayer.actual_stats ? {
      fantasy_points: {
        ppr: matchupPlayer.actual_stats.fantasy_points,
        standard: matchupPlayer.actual_stats.fantasy_points,
        half_ppr: matchupPlayer.actual_stats.fantasy_points
      },
      passing: { yards: 0, touchdowns: 0, interceptions: 0, attempts: 0, completions: 0 },
      rushing: { yards: 0, touchdowns: 0, attempts: 0 },
      receiving: { yards: 0, touchdowns: 0, receptions: 0, targets: 0 },
      performance: { vs_projection: null }
    } : null
  });

  // Organize players by position based on roster_positions order
  const organizePlayersByRosterSlots = (playersToOrganize: Player[]) => {
    if (!rosterPositions.length) {
      return playersToOrganize.map(player => ({ player, slot: player.position }));
    }

    const starters = playersToOrganize.filter(p => p.is_starter);
    const bench = playersToOrganize.filter(p => !p.is_starter);

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
      } else if (teamType === 'opponent') {
        // Empty slot for opponent
        organizedPlayers.push({
          player: {
            sleeper_id: `opp-empty-${slot}`,
            player_name: 'Empty Slot',
            position: slot,
            team: '',
            is_starter: true,
            player_details: {
              age: null,
              height: null,
              weight: null,
              college: null,
              years_exp: null,
              status: 'Active',
              fantasy_positions: [slot]
            },
            external_ids: {
              espn_id: null,
              rotowire_id: null,
              fantasy_data_id: null,
              yahoo_id: null,
              stats_id: null
            },
            projections: null,
            actual_stats: null
          } as Player,
          slot
        });
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

  // Organize opponent players from matchup data
  const organizeOpponentBySlots = () => {
    if (!matchup?.opponent_roster?.players || !rosterPositions.length) {
      return matchup?.opponent_roster?.players.map(player => ({
        player: convertMatchupPlayerToPlayer(player, player.position || 'UNKNOWN'),
        slot: player.position || 'UNKNOWN'
      })) || [];
    }

    const availablePlayers = [...matchup.opponent_roster.players];
    const organizedPlayers: { player: Player; slot: string }[] = [];

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
            player_details: {
              age: null,
              height: null,
              weight: null,
              college: null,
              years_exp: null,
              status: 'Active',
              fantasy_positions: [slot]
            },
            external_ids: {
              espn_id: null,
              rotowire_id: null,
              fantasy_data_id: null,
              yahoo_id: null,
              stats_id: null
            },
            projections: null,
            actual_stats: null
          } as Player,
          slot
        });
      }
    });

    return organizedPlayers;
  };

  // Get the appropriate players and organization
  const getTeamData = () => {
    if (teamType === 'user') {
      if (!players?.length) {
        return { organizedPlayers: [], teamName: 'Your Lineup', record: '' };
      }
      return {
        organizedPlayers: organizePlayersByRosterSlots(players),
        teamName: 'Your Lineup',
        record: teamRecord || ''
      };
    } else {
      // If players are provided, use them (from new consolidated API)
      if (players?.length) {
        return {
          organizedPlayers: organizePlayersByRosterSlots(players),
          teamName: 'Opponent',
          record: teamRecord || ''
        };
      }

      // Otherwise, fall back to old matchup loading logic
      if (loading) {
        return { loading: true };
      }
      if (error) {
        return { error };
      }
      if (!matchup?.opponent_roster) {
        return { byeWeek: true };
      }
      return {
        organizedPlayers: organizeOpponentBySlots(),
        teamName: 'Opponent',
        record: teamRecord || matchup.opponent_roster.record || ''
      };
    }
  };

  const teamData = getTeamData();

  // Loading state
  if ('loading' in teamData && teamData.loading) {
    return (
      <Card>
        <div className="flex items-center justify-center py-8">
          <LoadingSpinner size="md" />
        </div>
      </Card>
    );
  }

  // Error state
  if ('error' in teamData && teamData.error) {
    return (
      <Card>
        <div className="text-center py-8 text-danger-400">
          <p>{teamData.error}</p>
        </div>
      </Card>
    );
  }

  // Bye week state
  if ('byeWeek' in teamData && teamData.byeWeek) {
    return (
      <Card>
        {showTitle && <h2 className="text-xl font-bold text-white mb-4">Opponent</h2>}
        <div className="text-center py-8 text-dark-400">
          <p className="text-lg">🏖️ Bye Week</p>
          <p className="text-sm">No opponent this week</p>
        </div>
      </Card>
    );
  }

  // No lineup available
  if (!teamData.organizedPlayers?.length) {
    return (
      <Card>
        {showTitle && <h2 className="text-xl font-bold text-white mb-4">{teamData.teamName}</h2>}
        <div className="text-center py-8 text-dark-400">
          <p>No lineup available</p>
        </div>
      </Card>
    );
  }

  const { organizedPlayers, teamName, record } = teamData;
  const startingPlayers = organizedPlayers.filter(({ slot }) => slot !== 'BN');
  const benchPlayers = organizedPlayers.filter(({ slot }) => slot === 'BN');

  // Calculate totals for starting lineup (exclude empty slots for opponent)
  const validPlayers = startingPlayers.filter(({ player }) =>
    player.sleeper_id && !player.sleeper_id.startsWith('opp-empty')
  );
  const totalProjected = validPlayers.reduce((sum, { player }) =>
    sum + (player.projections?.fantasy_points ?? 0), 0);
  const totalActual = validPlayers.reduce((sum, { player }) =>
    sum + (player.actual_stats?.fantasy_points?.ppr ?? 0), 0);
  const hasActualData = validPlayers.some(({ player }) => player.actual_stats !== null);

  return (
    <div className="space-y-4">
      {/* Starting Lineup */}
      <Card>
        {showTitle && (
          <h2 className={`text-lg font-bold text-white mb-3 ${isFlipped ? 'text-right' : 'text-left'}`}>
            {teamName} {record && `(${record})`}
          </h2>
        )}
        <div className="space-y-1">
          {startingPlayers.map(({ player, slot }, index) => (
            <PlayerCard
              key={`${player.sleeper_id}-${index}`}
              player={player}
              rosterSlot={slot}
              reversed={isFlipped}
            />
          ))}
        </div>
        {/* Totals */}
        <div className="mt-4 pt-4 border-t border-dark-700">
          <div className={`flex ${isFlipped ? 'flex-row-reverse' : ''} justify-between items-center text-sm`}>
            <span className="text-dark-400">Total:</span>
            <div className={`flex items-center space-x-4 ${isFlipped ? 'flex-row-reverse space-x-reverse' : ''}`}>
              <div className="text-center">
                <div className="text-success-400 font-medium">
                  {totalProjected.toFixed(2)}
                </div>
                <div className="text-xs text-dark-500">Proj</div>
              </div>
              {hasActualData && (
                <div className="text-center">
                  <div className="text-primary-400 font-medium">
                    {totalActual.toFixed(2)}
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
                    {totalActual > totalProjected ? '+' : ''}{(totalActual - totalProjected).toFixed(2)}
                  </div>
                  <div className="text-xs text-dark-500">Diff</div>
                </div>
              )}
            </div>
          </div>
        </div>
      </Card>

      {/* Bench */}
      {benchPlayers.length > 0 && teamType === 'user' && (
        <Card>
          <h2 className={`text-lg font-bold text-white mb-3 ${isFlipped ? 'text-right' : 'text-left'}`}>
            Bench
          </h2>
          <div className="space-y-1">
            {benchPlayers.map(({ player, slot }, index) => (
              <PlayerCard
                key={`${player.sleeper_id}-bench-${index}`}
                player={player}
                rosterSlot={slot}
                reversed={isFlipped}
              />
            ))}
          </div>
        </Card>
      )}
    </div>
  );
};