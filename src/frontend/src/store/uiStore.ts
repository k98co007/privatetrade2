import { create } from 'zustand';

import type { NetworkState } from '../domain/types';

export type UiToast = {
  id: string;
  message: string;
};

export type UiStore = {
  toastQueue: UiToast[];
  networkState: NetworkState;
  lastSseHeartbeatAt: string | null;
  pushToast: (message: string) => void;
  shiftToast: () => void;
  setNetworkState: (state: NetworkState) => void;
  setLastHeartbeat: (timestamp: string) => void;
};

export const useUiStore = create<UiStore>((set) => ({
  toastQueue: [],
  networkState: 'online',
  lastSseHeartbeatAt: null,

  pushToast: (message) =>
    set((state) => ({
      toastQueue: [...state.toastQueue, { id: `${Date.now()}-${Math.random()}`, message }],
    })),

  shiftToast: () =>
    set((state) => ({
      toastQueue: state.toastQueue.slice(1),
    })),

  setNetworkState: (networkState) => set({ networkState }),
  setLastHeartbeat: (lastSseHeartbeatAt) => set({ lastSseHeartbeatAt }),
}));
