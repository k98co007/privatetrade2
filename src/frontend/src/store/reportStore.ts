import { create } from 'zustand';

import type { ComprehensiveReport, ReportCacheEntry, UiError } from '../domain/types';

type ReportStore = {
  cacheBySimulationId: Record<string, ReportCacheEntry>;
  activeSimulationId: string | null;
  isLoading: boolean;
  error: UiError | null;
  upsertCache: (simulationId: string, report: ComprehensiveReport, fetchedAt?: number) => void;
  setActiveSimulationId: (simulationId: string | null) => void;
  setLoading: (isLoading: boolean) => void;
  setError: (error: UiError | null) => void;
};

export const useReportStore = create<ReportStore>((set) => ({
  cacheBySimulationId: {},
  activeSimulationId: null,
  isLoading: false,
  error: null,

  upsertCache: (simulationId, report, fetchedAt = Date.now()) => {
    set((state) => ({
      cacheBySimulationId: {
        ...state.cacheBySimulationId,
        [simulationId]: {
          simulationId,
          schemaVersion: report.schemaVersion,
          fetchedAt,
          report,
        },
      },
      activeSimulationId: simulationId,
      error: null,
    }));
  },

  setActiveSimulationId: (simulationId) => set({ activeSimulationId: simulationId }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
}));
