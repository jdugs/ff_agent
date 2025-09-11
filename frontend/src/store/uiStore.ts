import { create } from 'zustand';
import type { Player } from '@/lib/types';

interface UIState {
  // Modal states
  selectedPlayer: Player | null;
  isPlayerModalOpen: boolean;
  
  // Loading states
  isPageLoading: boolean;
  
  // Navigation
  sidebarOpen: boolean;
  currentPage: string;
  
  // Notifications
  notifications: Notification[];
  
  // Actions
  openPlayerModal: (player: Player) => void;
  closePlayerModal: () => void;
  toggleSidebar: () => void;
  setCurrentPage: (page: string) => void;
  setPageLoading: (loading: boolean) => void;
  addNotification: (notification: Omit<Notification, 'id'>) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
}

interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
}

export const useUIStore = create<UIState>((set, get) => ({
  // Initial state
  selectedPlayer: null,
  isPlayerModalOpen: false,
  isPageLoading: false,
  sidebarOpen: false,
  currentPage: 'dashboard',
  notifications: [],

  // Actions
  openPlayerModal: (player: Player) => {
    set({ selectedPlayer: player, isPlayerModalOpen: true });
  },

  closePlayerModal: () => {
    set({ selectedPlayer: null, isPlayerModalOpen: false });
  },

  toggleSidebar: () => {
    set((state) => ({ sidebarOpen: !state.sidebarOpen }));
  },

  setCurrentPage: (page: string) => {
    set({ currentPage: page });
  },

  setPageLoading: (loading: boolean) => {
    set({ isPageLoading: loading });
  },

  addNotification: (notification: Omit<Notification, 'id'>) => {
    const id = Math.random().toString(36).substr(2, 9);
    const newNotification = { 
      ...notification, 
      id,
      duration: notification.duration || 5000 
    };
    
    set((state) => ({
      notifications: [...state.notifications, newNotification]
    }));

    // Auto-remove notification after duration
    if (newNotification.duration > 0) {
      setTimeout(() => {
        get().removeNotification(id);
      }, newNotification.duration);
    }
  },

  removeNotification: (id: string) => {
    set((state) => ({
      notifications: state.notifications.filter(n => n.id !== id)
    }));
  },

  clearNotifications: () => {
    set({ notifications: [] });
  },
}));
