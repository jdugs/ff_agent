import React from 'react';
import type { TeamDashboard } from '@/lib/types';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { formatPoints } from '@/lib/utils';
import { TEAM_HEALTH_CONFIG } from '@/lib/constants';
import { TrendingUp, Target, Award } from 'lucide-react';

interface TeamOverviewProps {
  team: TeamDashboard;
}

export const TeamOverview: React.FC<TeamOverviewProps> = ({ team }) => {
  const { roster_summary, metadata, quick_stats } = team.data;
  
  // Calculate team health based on projections and provider coverage
  const teamHealth = 'good'; // Default for now - could calculate based on confidence scores
  const healthConfig = TEAM_HEALTH_CONFIG[teamHealth] || { icon: '💪', color: 'text-success-400' };
  
  // Format record string
  const recordString = `${roster_summary.team_record.wins}-${roster_summary.team_record.losses}${roster_summary.team_record.ties > 0 ? `-${roster_summary.team_record.ties}` : ''}`;
  
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {/* Team Record */}
      <Card>
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-primary-500/20 rounded-lg">
            <Award className="w-6 h-6 text-primary-400" />
          </div>
          <div>
            <div className="text-2xl font-bold text-white">
              {recordString}
            </div>
            <div className="text-sm text-dark-400">
              {formatPoints(roster_summary.team_record.points_for)} PF • {formatPoints(roster_summary.team_record.points_against)} PA
            </div>
          </div>
        </div>
      </Card>

      {/* Weekly Projections */}
      <Card>
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-success-500/20 rounded-lg">
            <TrendingUp className="w-6 h-6 text-success-400" />
          </div>
          <div>
            <div className="text-2xl font-bold text-white">
              {formatPoints(roster_summary.projected_points_total)}
            </div>
            <div className="text-sm text-dark-400">
              {metadata.week ? `Week ${metadata.week}` : `${metadata.season} Season`} Projection
            </div>
            <Badge variant="success" size="sm">
              Consensus
            </Badge>
          </div>
        </div>
      </Card>

      {/* Team Composition */}
      <Card>
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-warning-500/20 rounded-lg">
            <Target className="w-6 h-6 text-warning-400" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-2xl">{healthConfig.icon}</span>
              <span className={`text-lg font-medium ${healthConfig.color}`}>
                {roster_summary.starters_count} Starters
              </span>
            </div>
            <div className="text-sm text-dark-400">
              {roster_summary.bench_count} bench • {roster_summary.total_players} total
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};
