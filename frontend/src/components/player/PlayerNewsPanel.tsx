import React from 'react';
import type { Player } from '@/lib/types';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { formatTimeAgo } from '@/lib/utils';

interface PlayerNewsPanelProps {
  player: Player;
}

export const PlayerNewsPanel: React.FC<PlayerNewsPanelProps> = ({ player }) => {
  const news = player.recent_news || player.news_alerts || [];
  
  if (news.length === 0) {
    return (
      <div className="text-center py-12 text-dark-400">
        <p>No recent news for this player</p>
        <div className="mt-4 text-sm text-dark-300">
          <p>Player Details:</p>
          <div className="mt-2 space-y-1 text-xs">
            {player.player_details?.college && (
              <p><span className="text-dark-400">College:</span> {player.player_details.college}</p>
            )}
            {player.player_details?.years_exp !== null && (
              <p><span className="text-dark-400">Experience:</span> {player.player_details.years_exp} years</p>
            )}
            {player.player_details?.age && (
              <p><span className="text-dark-400">Age:</span> {player.player_details.age}</p>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {news.map((newsItem, index) => (
        <Card key={index} className="bg-dark-700">
          <div className="space-y-3">
            <div className="flex items-start justify-between">
              <h4 className="font-medium text-white flex-1 pr-4">
                {newsItem.title}
              </h4>
              <div className="flex items-center space-x-2">
                <Badge 
                  variant={
                    newsItem.severity === 'high' ? 'danger' :
                    newsItem.severity === 'medium' ? 'warning' : 'info'
                  }
                  size="sm"
                >
                  {(newsItem as any).event_type || (newsItem as any).type || 'Update'}
                </Badge>
              </div>
            </div>
            
            {(newsItem as any).description && (
              <p className="text-sm text-dark-300">
                {(newsItem as any).description}
              </p>
            )}
            
            <div className="flex items-center justify-between text-xs">
              <span className="text-dark-400">
                {(newsItem as any).source_name || 'System'}
              </span>
              <span className="text-dark-400">
                {formatTimeAgo(newsItem.timestamp)}
              </span>
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
};