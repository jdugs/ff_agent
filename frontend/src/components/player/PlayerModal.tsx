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
  { id: 'stats', label: 'Actual Stats' },
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

              {selectedPlayer.actual_stats && (
                <div>
                  <span className="text-dark-400">Actual: </span>
                  <span className="text-primary-400 font-medium">
                    {formatPoints(selectedPlayer.actual_stats.fantasy_points.ppr)} pts
                  </span>
                  {selectedPlayer.projections && (
                    <span className={`text-xs ml-1 ${
                      (selectedPlayer.actual_stats.fantasy_points.ppr - selectedPlayer.projections.fantasy_points) > 0 
                        ? 'text-success-400' 
                        : 'text-danger-400'
                    }`}>
                      ({(selectedPlayer.actual_stats.fantasy_points.ppr - selectedPlayer.projections.fantasy_points) > 0 ? '+' : ''}
                      {formatPoints(selectedPlayer.actual_stats.fantasy_points.ppr - selectedPlayer.projections.fantasy_points)})
                    </span>
                  )}
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
          {activeTab === 'stats' && (
            <div className="space-y-4">
              {selectedPlayer.actual_stats ? (
                <>
                  {/* Fantasy Points */}
                  <Card>
                    <h3 className="text-lg font-semibold text-white mb-3">Fantasy Points</h3>
                    <div className="grid grid-cols-3 gap-4">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-primary-400">
                          {formatPoints(selectedPlayer.actual_stats.fantasy_points.ppr)}
                        </div>
                        <div className="text-xs text-dark-400">PPR</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-primary-400">
                          {formatPoints(selectedPlayer.actual_stats.fantasy_points.half_ppr)}
                        </div>
                        <div className="text-xs text-dark-400">Half PPR</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-primary-400">
                          {formatPoints(selectedPlayer.actual_stats.fantasy_points.standard)}
                        </div>
                        <div className="text-xs text-dark-400">Standard</div>
                      </div>
                    </div>
                  </Card>

                  {/* Detailed Stats */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* Passing Stats */}
                    {(selectedPlayer.actual_stats.passing.yards > 0 || selectedPlayer.actual_stats.passing.touchdowns > 0) && (
                      <Card>
                        <h4 className="font-semibold text-white mb-2">Passing</h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-dark-400">Yards:</span>
                            <span className="text-white">{selectedPlayer.actual_stats.passing.yards}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-dark-400">TDs:</span>
                            <span className="text-white">{selectedPlayer.actual_stats.passing.touchdowns}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-dark-400">INTs:</span>
                            <span className="text-white">{selectedPlayer.actual_stats.passing.interceptions}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-dark-400">Comp/Att:</span>
                            <span className="text-white">
                              {selectedPlayer.actual_stats.passing.completions}/{selectedPlayer.actual_stats.passing.attempts}
                            </span>
                          </div>
                        </div>
                      </Card>
                    )}

                    {/* Rushing Stats */}
                    {(selectedPlayer.actual_stats.rushing.yards > 0 || selectedPlayer.actual_stats.rushing.touchdowns > 0) && (
                      <Card>
                        <h4 className="font-semibold text-white mb-2">Rushing</h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-dark-400">Yards:</span>
                            <span className="text-white">{selectedPlayer.actual_stats.rushing.yards}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-dark-400">TDs:</span>
                            <span className="text-white">{selectedPlayer.actual_stats.rushing.touchdowns}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-dark-400">Attempts:</span>
                            <span className="text-white">{selectedPlayer.actual_stats.rushing.attempts}</span>
                          </div>
                        </div>
                      </Card>
                    )}

                    {/* Receiving Stats */}
                    {(selectedPlayer.actual_stats.receiving.yards > 0 || selectedPlayer.actual_stats.receiving.touchdowns > 0 || selectedPlayer.actual_stats.receiving.receptions > 0) && (
                      <Card>
                        <h4 className="font-semibold text-white mb-2">Receiving</h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-dark-400">Yards:</span>
                            <span className="text-white">{selectedPlayer.actual_stats.receiving.yards}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-dark-400">TDs:</span>
                            <span className="text-white">{selectedPlayer.actual_stats.receiving.touchdowns}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-dark-400">Rec/Tgt:</span>
                            <span className="text-white">
                              {selectedPlayer.actual_stats.receiving.receptions}/{selectedPlayer.actual_stats.receiving.targets}
                            </span>
                          </div>
                        </div>
                      </Card>
                    )}
                  </div>

                  {/* Performance vs Projection */}
                  {selectedPlayer.projections && (
                    <Card className="bg-info-500/10 border-info-500/30">
                      <h4 className="font-semibold text-info-400 mb-2">Performance vs Projection</h4>
                      <div className="flex items-center justify-between">
                        <span className="text-dark-400">Actual vs Projected:</span>
                        <span className={`font-medium ${
                          (selectedPlayer.actual_stats.fantasy_points.ppr - selectedPlayer.projections.fantasy_points) > 0 
                            ? 'text-success-400' 
                            : 'text-danger-400'
                        }`}>
                          {formatPoints(selectedPlayer.actual_stats.fantasy_points.ppr)} vs {formatPoints(selectedPlayer.projections.fantasy_points)}
                          ({(selectedPlayer.actual_stats.fantasy_points.ppr - selectedPlayer.projections.fantasy_points) > 0 ? '+' : ''}
                          {formatPoints(selectedPlayer.actual_stats.fantasy_points.ppr - selectedPlayer.projections.fantasy_points)})
                        </span>
                      </div>
                    </Card>
                  )}
                </>
              ) : (
                <div className="text-center py-12 text-dark-400">
                  <p>No actual stats available yet</p>
                  <p className="text-sm mt-1">Stats will appear after the player's game</p>
                </div>
              )}
            </div>
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