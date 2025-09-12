import React from 'react';
import type { Player } from '@/lib/types';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { formatTimeAgo } from '@/lib/utils';
import { Newspaper } from 'lucide-react';

interface RecentNewsProps {
  players: Player[];
}

export const RecentNews: React.FC<RecentNewsProps> = ({ players }) => {
  // Aggregate all news from starters
  const allNews = players
    .flatMap(player => 
      (player.recent_news || player.news_alerts || []).map(news => ({ 
        ...news, 
        playerName: player.player_name || 'Unknown Player' 
      }))
    )
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
    .slice(0, 5);

  return (
    <Card>
      <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
        <Newspaper className="w-5 h-5 mr-2" />
        Recent News
      </h3>
      
      {allNews.length === 0 ? (
        <p className="text-dark-400 text-sm">No recent news for your players</p>
      ) : (
        <div className="space-y-3">
          {allNews.map((news, index) => (
            <div key={index} className="border-l-2 border-primary-500 pl-3">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="text-sm font-medium text-white">
                    {news.playerName}
                  </p>
                  <p className="text-sm text-dark-300 mt-1">
                    {news.title}
                  </p>
                  <div className="flex items-center space-x-2 mt-2">
                    <Badge 
                      variant={news.severity === 'high' ? 'danger' : 'warning'} 
                      size="sm"
                    >
                      {(news as any).event_type || (news as any).type || 'Update'}
                    </Badge>
                    <span className="text-xs text-dark-500">
                      {formatTimeAgo(news.timestamp)}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
};