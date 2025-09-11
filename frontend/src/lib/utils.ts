import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
return twMerge(clsx(inputs));
}
  
export function formatPoints(points: number | undefined): string {
  if (!points) return '0.0';
  return points.toFixed(1);
}

export function formatRecord(record: string): string {
  return record.replace(/-/g, ' - ');
}

export function getPositionColor(position: string): string {
  const colors = {
    QB: 'text-red-400 bg-red-500/10 border-red-500/30',
    RB: 'text-green-400 bg-green-500/10 border-green-500/30',
    WR: 'text-blue-400 bg-blue-500/10 border-blue-500/30',
    TE: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30',
    K: 'text-purple-400 bg-purple-500/10 border-purple-500/30',
    DST: 'text-gray-400 bg-gray-500/10 border-gray-500/30',
  };
  return colors[position as keyof typeof colors] || colors.DST;
}

export function getStatusColor(recommendation?: string, redFlags: string[] = []): string {
  if (redFlags.length > 0) return 'border-red-500/60 bg-red-500/20';
  
  switch (recommendation) {
    case 'start':
      return 'border-green-500/60 bg-green-500/20';
    case 'flex':
      return 'border-yellow-500/60 bg-yellow-500/20';
    case 'sit':
      return 'border-red-500/60 bg-red-500/20';
    default:
      return 'border-dark-600 bg-dark-800';
  }
}

export function getStatusIcon(recommendation?: string, redFlags: string[] = []): string {
  if (redFlags.length > 0) return '⚠️';
  
  switch (recommendation) {
    case 'start':
      return '⭐';
    case 'flex':
      return '🤔';
    case 'sit':
      return '❌';
    default:
      return '➖';
  }
}

export function formatTimeAgo(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
  
  if (diffInHours < 1) return 'Just now';
  if (diffInHours < 24) return `${diffInHours}h ago`;
  if (diffInHours < 168) return `${Math.floor(diffInHours / 24)}d ago`;
  return date.toLocaleDateString();
}

export function getRankTrend(current?: number, previous?: number): 'up' | 'down' | 'stable' {
  if (!current || !previous) return 'stable';
  if (current < previous) return 'up'; // Lower rank number = better
  if (current > previous) return 'down';
  return 'stable';
}

export function getTrendIcon(trend: 'up' | 'down' | 'stable'): string {
  switch (trend) {
    case 'up': return '↗️';
    case 'down': return '↘️';
    default: return '→';
  }
}