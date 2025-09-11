import React from 'react';
import type { Player } from '@/lib/types';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { formatTimeAgo } from '@/lib/utils';

interface PlayerNewsPanelProps {
  player: Player;
}

export const PlayerNewsPanel: React.FC<PlayerNewsPanelProps> = ({ player }) => {
  if (player.recent_news.length === 0) {
    return (
      <div className="text-center py-12 text-dark-400">
        <p>No recent news for this player</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {player.recent_news.map((news, index) => (
        <Card key={index} className="bg-dark-700">
          <div className="space-y-3">
            <div className="flex items-start justify-between">
              <h4 className="font-medium text-white flex-1 pr-4">
                {news.title}
              </h4>
              <div className="flex items-center space-x-2">
                <Badge 
                  variant={
                    news.severity === 'high' ? 'danger' :
                    news.severity === 'medium' ? 'warning' : 'info'
                  }
                  size="sm"
                >
                  {news.event_type}
                </Badge>
              </div>
            </div>
            
            {news.description && (
              <p className="text-sm text-dark-300">
                {news.description}
              </p>
            )}
            
            <div className="flex items-center justify-between text-xs">
              <span className="text-dark-400">
                {news.source_name}
              </span>
              <span className="text-dark-400">
                {formatTimeAgo(news.timestamp)}
              </span>
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
};