import { create } from 'zustand';

import type { EventItem, ProgressState, SimulationMeta, SimulationStatus, UiError } from '../domain/types';

type SimulationStateEntry = {
  meta: SimulationMeta;
  status: SimulationStatus;
  progress: ProgressState;
  lastAppliedEventId: number;
  eventIds: number[];
  error: UiError | null;
};

export type SimulationStore = {
  currentSimulationId: string | null;
  byId: Record<string, SimulationStateEntry>;
  eventsById: Record<number, EventItem>;
  createSimulation: (meta: SimulationMeta) => void;
  updateStatus: (simulationId: string, status: SimulationStatus) => void;
  applyProgress: (simulationId: string, progress: ProgressState, eventId: number) => void;
  appendEvent: (simulationId: string, event: EventItem) => void;
  markEventApplied: (simulationId: string, eventId: number) => void;
  setError: (simulationId: string, error: UiError | null) => void;
  clearEvents: (simulationId: string) => void;
};

const EMPTY_PROGRESS: ProgressState = {
  currentDay: 0,
  totalDays: 1,
  progressPct: 0,
  tradingDate: null,
};

const MAX_EVENT_ITEMS = 500;

export const useSimulationStore = create<SimulationStore>((set, get) => ({
  currentSimulationId: null,
  byId: {},
  eventsById: {},

  createSimulation: (meta) => {
    set((state) => ({
      currentSimulationId: meta.simulationId,
      byId: {
        ...state.byId,
        [meta.simulationId]: {
          meta,
          status: 'starting',
          progress: EMPTY_PROGRESS,
          lastAppliedEventId: 0,
          eventIds: [],
          error: null,
        },
      },
    }));
  },

  updateStatus: (simulationId, status) => {
    set((state) => {
      const current = state.byId[simulationId];
      if (!current) {
        return state;
      }
      return {
        byId: {
          ...state.byId,
          [simulationId]: {
            ...current,
            status,
          },
        },
      };
    });
  },

  applyProgress: (simulationId, progress, eventId) => {
    set((state) => {
      const current = state.byId[simulationId];
      if (!current || eventId <= current.lastAppliedEventId) {
        return state;
      }
      return {
        byId: {
          ...state.byId,
          [simulationId]: {
            ...current,
            status: 'running',
            progress,
            lastAppliedEventId: eventId,
          },
        },
      };
    });
  },

  appendEvent: (simulationId, event) => {
    set((state) => {
      const current = state.byId[simulationId];
      if (!current || event.eventId <= current.lastAppliedEventId) {
        return state;
      }

      const nextEventIds = [...current.eventIds, event.eventId];
      const nextEventsById: Record<number, EventItem> = {
        ...state.eventsById,
        [event.eventId]: event,
      };

      if (nextEventIds.length > MAX_EVENT_ITEMS) {
        const removeIds = nextEventIds.splice(0, nextEventIds.length - MAX_EVENT_ITEMS);
        removeIds.forEach((removeId) => {
          delete nextEventsById[removeId];
        });
      }

      return {
        byId: {
          ...state.byId,
          [simulationId]: {
            ...current,
            eventIds: nextEventIds,
            lastAppliedEventId: event.eventId,
          },
        },
        eventsById: nextEventsById,
      };
    });
  },

  markEventApplied: (simulationId, eventId) => {
    set((state) => {
      const current = state.byId[simulationId];
      if (!current || eventId <= current.lastAppliedEventId) {
        return state;
      }
      return {
        byId: {
          ...state.byId,
          [simulationId]: {
            ...current,
            lastAppliedEventId: eventId,
          },
        },
      };
    });
  },

  setError: (simulationId, error) => {
    set((state) => {
      const current = state.byId[simulationId];
      if (!current) {
        return state;
      }
      return {
        byId: {
          ...state.byId,
          [simulationId]: {
            ...current,
            status: error ? 'error' : current.status,
            error,
          },
        },
      };
    });
  },

  clearEvents: (simulationId) => {
    set((state) => {
      const current = state.byId[simulationId];
      if (!current) {
        return state;
      }
      const nextEventsById = { ...state.eventsById };
      current.eventIds.forEach((id) => {
        delete nextEventsById[id];
      });
      return {
        byId: {
          ...state.byId,
          [simulationId]: {
            ...current,
            eventIds: [],
          },
        },
        eventsById: nextEventsById,
      };
    });
  },
}));

export function getSimulationLastEventId(simulationId: string): number {
  const state = useSimulationStore.getState();
  return state.byId[simulationId]?.lastAppliedEventId ?? 0;
}
