import { useCallback } from 'react';

import { toUiError } from '../domain/errorMapper';
import { normalizeReport } from '../domain/normalizers';
import type { ComprehensiveReport } from '../domain/types';
import { getReport } from '../services/reportApi';
import { useReportStore } from '../store/reportStore';
import { isFresh } from '../utils/time';

const REPORT_TTL_MS = 30_000;

export function useReportQuery() {
  const cacheBySimulationId = useReportStore((state) => state.cacheBySimulationId);
  const setLoading = useReportStore((state) => state.setLoading);
  const setError = useReportStore((state) => state.setError);
  const upsertCache = useReportStore((state) => state.upsertCache);
  const setActiveSimulationId = useReportStore((state) => state.setActiveSimulationId);

  const fetchNetwork = useCallback(
    async (simulationId: string): Promise<ComprehensiveReport> => {
      setLoading(true);
      try {
        const response = await getReport(simulationId, { schemaVersion: '1.0' });
        const report = normalizeReport(response);
        upsertCache(simulationId, report, Date.now());
        setActiveSimulationId(simulationId);
        return report;
      } catch (error) {
        setError(toUiError(error));
        throw error;
      } finally {
        setLoading(false);
      }
    },
    [setLoading, setError, upsertCache, setActiveSimulationId],
  );

  const loadReport = useCallback(
    async (simulationId: string): Promise<ComprehensiveReport> => {
      const cached = cacheBySimulationId[simulationId];
      if (cached && isFresh(cached.fetchedAt, REPORT_TTL_MS)) {
        setActiveSimulationId(simulationId);
        void fetchNetwork(simulationId);
        return cached.report;
      }
      return fetchNetwork(simulationId);
    },
    [cacheBySimulationId, setActiveSimulationId, fetchNetwork],
  );

  const refreshReport = useCallback(
    async (simulationId: string): Promise<void> => {
      await fetchNetwork(simulationId);
    },
    [fetchNetwork],
  );

  return {
    loadReport,
    refreshReport,
  };
}
