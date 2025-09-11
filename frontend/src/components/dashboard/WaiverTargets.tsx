import React from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { TrendingUp, Plus } from 'lucide-react';

// Mock data - replace with real API call
const mockWaiverTargets = [
  { name: 'J.K. Dobbins', position: 'RB', team: 'LAC', trend: 'up', owned: '67%' },
  { name: 'Wan\'Dale Robinson', position: 'WR', team: 'NYG', trend: 'up', owned: '23%' },
  { name: 'David Njoku', position: 'TE', team: 'CLE', trend: 'stable', owned: '45%' },
];

export const WaiverTargets: React.FC = () => {
  return (
    <Card>
      <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
        <Plus className="w-5 h-5 mr-2" />
        Waiver Targets
      </h3>
      
      <div className="space-y-3">
        {mockWaiverTargets.map((target, index) => (
          <div 
            key={index} 
            className="flex items-center justify-between p-3 bg-dark-700 rounded-lg hover:bg-dark-600 transition-colors cursor-pointer"
          >
            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-1">
                <TrendingUp className="w-4 h-4 text-success-400" />
                <Badge variant="info" size="sm">
                  {target.position}
                </Badge>
              </div>
              <div>
                <p className="text-sm font-medium text-white">
                  {target.name}
                </p>
                <p className="text-xs text-dark-400">
                  {target.team} • {target.owned} owned
                </p>
              </div>
            </div>
            <div className="text-xs text-success-400">
              📈 Rising
            </div>
          </div>
        ))}
      </div>
      
      <div className="mt-4 pt-3 border-t border-dark-700">
        <button className="text-sm text-primary-400 hover:text-primary-300 transition-colors">
          View all waiver targets →
        </button>
      </div>
    </Card>
  );
};