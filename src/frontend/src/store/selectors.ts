import { useMemo } from 'react';

import type { EventItem } from '../domain/types';
import { useReportStore } from './reportStore';
import { useSimulationStore } from './simulationStore';

export function useCurrentSimulation() {
  return useSimulationStore((state) => {
    if (!state.currentSimulationId) {
      return null;
    }
    return state.byId[state.currentSimulationId] ?? null;
  });
}

export function useSimulationById(simulationId: string | undefined) {
  return useSimulationStore((state) => (simulationId ? state.byId[simulationId] ?? null : null));
}

export function useSimulationEvents(simulationId: string | undefined): EventItem[] {
  const entry = useSimulationStore((state) => (simulationId ? state.byId[simulationId] ?? null : null));
  const eventsById = useSimulationStore((state) => state.eventsById);

  return useMemo(() => {
    if (!entry) {
      return [];
    }
    return entry.eventIds
      .map((id) => eventsById[id])
      .filter((item): item is EventItem => Boolean(item));
  }, [entry, eventsById]);
}

export function useActiveReport() {
  return useReportStore((state) => {
    if (!state.activeSimulationId) {
      return null;
    }
    return state.cacheBySimulationId[state.activeSimulationId] ?? null;
  });
}
