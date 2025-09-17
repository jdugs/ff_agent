'use client';

import React, { useEffect, useState } from 'react';
import { MatchupHeader } from './MatchupHeader';
import { MatchupTeam } from './MatchupTeam';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Card } from '@/components/ui/Card';
import { useTeamStore } from '@/store/teamStore';
import { ApiClient } from '@/lib/api';
import type { Player, TeamDashboard, Matchup } from '@/lib/types';

interface MatchupViewProps {
  // Optional week parameter - defaults to current week
  week?: number;
}

export const MatchupView: React.FC<MatchupViewProps> = ({ week }) => {
  const { selectedLeagueId, selectedUserId, currentWeek } = useTeamStore();
  const [selectedWeek, setSelectedWeek] = useState<number>(week || currentWeek || 1);
  const [userTeam, setUserTeam] = useState<TeamDashboard | null>(null);
  const [opponentTeam, setOpponentTeam] = useState<TeamDashboard | null>(null);
  const [opponentId, setOpponentId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Update selectedWeek when week prop or currentWeek changes
  useEffect(() => {
    setSelectedWeek(week || currentWeek || 1);
  }, [week, currentWeek]);

  // Load both teams simultaneously using the unified API
  useEffect(() => {
    const loadMatchupData = async () => {
      if (!selectedLeagueId || !selectedUserId || !selectedWeek) return;

      setLoading(true);
      setError(null);

      try {
        // Step 1: Load user team data
        const userTeamData = await ApiClient.getTeamRoster(selectedLeagueId, selectedUserId, selectedWeek);
        setUserTeam(userTeamData);

        // Step 2: Get matchup info to find opponent
        try {
          const matchupData = await ApiClient.getMyMatchup(selectedLeagueId, selectedWeek, selectedUserId);

          if (matchupData.opponent_roster?.owner_id) {
            const opponentOwnerId = matchupData.opponent_roster.owner_id;
            setOpponentId(opponentOwnerId);

            // Step 3: Load opponent team data using the same API
            const opponentTeamData = await ApiClient.getTeamRoster(selectedLeagueId, opponentOwnerId, selectedWeek);
            setOpponentTeam(opponentTeamData);
          } else {
            // Bye week - no opponent
            setOpponentTeam(null);
            setOpponentId(null);
          }
        } catch (matchupError) {
          console.warn('Could not load opponent data:', matchupError);
          // Still show user team even if opponent fails
          setOpponentTeam(null);
          setOpponentId(null);
        }

      } catch (err) {
        console.error('Failed to load matchup data:', err);
        setError('Failed to load matchup data');
      } finally {
        setLoading(false);
      }
    };

    loadMatchupData();
  }, [selectedLeagueId, selectedUserId, selectedWeek]);

  if (loading) {
    return (
      <Card>
        <div className="flex items-center justify-center py-8">
          <LoadingSpinner size="lg" />
          <span className="ml-3 text-white">Loading matchup...</span>
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

  if (!userTeam) {
    return (
      <Card>
        <div className="text-center py-8 text-dark-400">
          <p>No team data available</p>
        </div>
      </Card>
    );
  }

  // Extract players from team data
  const userPlayers = [...userTeam.data.lineup.starters, ...userTeam.data.lineup.bench];
  const opponentPlayers = opponentTeam ? opponentTeam.data.lineup.starters : []; // Only starters for opponent

  return (
    <div className="space-y-6">
      {/* Matchup Header with totals and week selector */}
      <MatchupHeader
        userPlayers={userTeam.data.lineup.starters}
        opponentPlayers={opponentPlayers}
        isByeWeek={!opponentTeam}
        selectedWeek={selectedWeek}
        currentWeek={currentWeek}
        onWeekChange={setSelectedWeek}
      />

      {/* Teams in symmetrical layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* User Team (Left side) */}
        <div>
          <MatchupTeam
            teamType="user"
            players={userPlayers}
            showTitle={true}
            teamRecord={`${userTeam.data.roster_summary.team_record.wins}-${userTeam.data.roster_summary.team_record.losses}-${userTeam.data.roster_summary.team_record.ties}`}
          />
        </div>

        {/* Opponent Team (Right side, flipped for symmetry) */}
        <div>
          {opponentTeam ? (
            <MatchupTeam
              teamType="opponent"
              players={opponentPlayers}
              isFlipped={true}
              showTitle={true}
              teamRecord={`${opponentTeam.data.roster_summary.team_record.wins}-${opponentTeam.data.roster_summary.team_record.losses}-${opponentTeam.data.roster_summary.team_record.ties}`}
            />
          ) : (
            <Card>
              <h2 className="text-xl font-bold text-white mb-4 text-right">Opponent</h2>
              <div className="text-center py-8 text-dark-400">
                <p className="text-lg">🏖️ Bye Week</p>
                <p className="text-sm">No opponent this week</p>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};