'use client';

import React from 'react';
import type { Player } from '@/lib/types';
import { useUIStore } from '@/store/uiStore';
import { Modal } from '@/components/ui/Modal';
import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/Card';
import { PlayerRankingsPanel } from './PlayerRankingsPanel';
import { PlayerProjectionsPanel } from './PlayerProjectionsPanel';
import { PlayerNewsPanel } from './PlayerNewsPanel';
import { getPositionColor, formatPoints } from '@/lib/utils';
import { useState } from 'react';

const tabs = [
  { id: 'rankings', label: 'Rankings' },
  { id: 'projections', label: 'Projections' },
  { id: 'news', label: 'News & Updates' },
  { id: 'trends', label: 'Trends' },
];

export const PlayerModal: React.FC = () => {
  const { selectedPlayer, isPlayerModalOpen, closePlayerModal } = useUIStore();
  const [activeTab, setActiveTab] = useState('rankings');

  if (!selectedPlayer) return null;

  const positionColor = getPositionColor(selectedPlayer.position);

  return (
    <Modal
      isOpen={isPlayerModalOpen}
      onClose={closePlayerModal}
      size="xl"
      className="max-h-[90vh] overflow-hidden"
    >
      <div className="space-y-6">
        {/* Player Header */}
        <div className="flex items-start space-x-4">
          <div className="w-16 h-16 bg-dark-700 rounded-lg flex items-center justify-center">
            <span className="text-2xl font-bold text-white">
              {selectedPlayer.position}
            </span>
          </div>
          
          <div className="flex-1">
            <div className="flex items-center space-x-3 mb-2">
              <h2 className="text-2xl font-bold text-white">
                {selectedPlayer.player_name}
              </h2>
              <Badge className={positionColor}>
                {selectedPlayer.position}
              </Badge>
              <Badge variant="info">
                {selectedPlayer.team}
              </Badge>
            </div>
            
            {selectedPlayer.player_details?.status && selectedPlayer.player_details.status !== 'Active' && (
              <p className="text-danger-400 mb-2">
                Status: {selectedPlayer.player_details.status}
              </p>
            )}
            
            <div className="flex items-center space-x-6 text-sm">
              {selectedPlayer.consensus_rank && (
                <div>
                  <span className="text-dark-400">Consensus Rank: </span>
                  <span className="text-white font-medium">
                    #{Math.round(selectedPlayer.consensus_rank)}
                  </span>
                </div>
              )}
              
              {(selectedPlayer.latest_projection || selectedPlayer.projections?.fantasy_points) && (
                <div>
                  <span className="text-dark-400">Projection: </span>
                  <span className="text-success-400 font-medium">
                    {formatPoints(selectedPlayer.projections?.fantasy_points || selectedPlayer.latest_projection || 0)} pts
                  </span>
                </div>
              )}

              {selectedPlayer.projections?.meta && (
                <div>
                  <span className="text-dark-400">Providers: </span>
                  <span className="text-primary-400 font-medium">
                    {selectedPlayer.projections.meta.provider_count}
                  </span>
                </div>
              )}
              
              {selectedPlayer.start_sit_recommendation && (
                <div>
                  <span className="text-dark-400">Recommendation: </span>
                  <Badge 
                    variant={
                      selectedPlayer.start_sit_recommendation === 'start' ? 'success' :
                      selectedPlayer.start_sit_recommendation === 'flex' ? 'warning' : 'danger'
                    }
                  >
                    {selectedPlayer.start_sit_recommendation.toUpperCase()}
                  </Badge>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Red Flags */}
        {(selectedPlayer.red_flags?.length || 0) > 0 && (
          <Card className="bg-danger-500/10 border-danger-500/30">
            <h3 className="text-lg font-semibold text-danger-400 mb-2">
              ⚠️ Alerts
            </h3>
            <ul className="space-y-1">
              {selectedPlayer.red_flags?.map((flag, index) => (
                <li key={index} className="text-sm text-danger-300">
                  • {flag}
                </li>
              ))}
            </ul>
          </Card>
        )}

        {/* Tabs */}
        <div className="border-b border-dark-700">
          <nav className="flex space-x-8">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab.id
                    ? 'border-primary-500 text-primary-400'
                    : 'border-transparent text-dark-400 hover:text-white'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="min-h-[300px] max-h-[400px] overflow-y-auto">
          {activeTab === 'rankings' && (
            <PlayerRankingsPanel player={selectedPlayer} />
          )}
          {activeTab === 'projections' && (
            <PlayerProjectionsPanel player={selectedPlayer} />
          )}
          {activeTab === 'news' && (
            <PlayerNewsPanel player={selectedPlayer} />
          )}
          {activeTab === 'trends' && (
            <div className="text-center py-12 text-dark-400">
              <p>Trends chart coming soon...</p>
            </div>
          )}
        </div>
      </div>
    </Modal>
  );
};