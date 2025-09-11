export const POSITIONS = ['QB', 'RB', 'WR', 'TE', 'K', 'DST'] as const;

export const POSITION_LIMITS = {
  QB: 1,
  RB: 2,
  WR: 2,
  TE: 1,
  FLEX: 1,
  K: 1,
  DST: 1,
} as const;

export const WEEKS = Array.from({ length: 18 }, (_, i) => i + 1);

export const CURRENT_SEASON = 2025;

export const STATUS_COLORS = {
  start: 'text-green-400 bg-green-500/20',
  flex: 'text-yellow-400 bg-yellow-500/20',
  sit: 'text-red-400 bg-red-500/20',
  injured: 'text-red-500 bg-red-600/30',
} as const;

export const TEAM_HEALTH_CONFIG = {
  good: { color: 'text-green-400', icon: '💚' },
  monitor: { color: 'text-yellow-400', icon: '⚠️' },
  concerning: { color: 'text-red-400', icon: '🚨' },
} as const;