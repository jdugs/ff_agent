import React from 'react';
import type { TeamDashboard } from '@/lib/types';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { formatPoints, formatRecord } from '@/lib/utils';
import { TEAM_HEALTH_CONFIG } from '@/lib/constants';
import { TrendingUp, Target, Award } from 'lucide-react';

interface TeamOverviewProps {
  team: TeamDashboard;
}

export const TeamOverview: React.FC<TeamOverviewProps> = ({ team }) => {
  const healthConfig = TEAM_HEALTH_CONFIG[team.team_summary.team_health];

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
              {formatRecord(team.team_record)}
            </div>
            <div className="text-sm text-dark-400">
              League Rank #{team.league_rank || '?'} / 12
            </div>
          </div>
        </div>
      </Card>

      {/* Weekly Outlook */}
      <Card>
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-success-500/20 rounded-lg">
            <TrendingUp className="w-6 h-6 text-success-400" />
          </div>
          <div>
            <div className="text-2xl font-bold text-white">
              {formatPoints(team.team_summary.projected_points)}
            </div>
            <div className="text-sm text-dark-400">
              Week {team.weekly_outlook.week} Projection
            </div>
            <Badge 
              variant={team.weekly_outlook.outlook === 'strong' ? 'success' : 
                      team.weekly_outlook.outlook === 'moderate' ? 'warning' : 'danger'}
              size="sm"
            >
              {team.weekly_outlook.outlook}
            </Badge>
          </div>
        </div>
      </Card>

      {/* Team Health */}
      <Card>
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-warning-500/20 rounded-lg">
            <Target className="w-6 h-6 text-warning-400" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-2xl">{healthConfig.icon}</span>
              <span className={`text-lg font-medium ${healthConfig.color}`}>
                {team.team_summary.team_health}
              </span>
            </div>
            <div className="text-sm text-dark-400">
              {team.team_summary.total_red_flags} alerts • {team.team_summary.injured_starters} injured starters
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};
