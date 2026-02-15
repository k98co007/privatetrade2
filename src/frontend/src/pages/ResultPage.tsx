import React, { useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { ComprehensiveReportCard } from '../components/ComprehensiveReportCard';
import { ProfitSummaryCard } from '../components/ProfitSummaryCard';
import { TradeHistoryTable } from '../components/TradeHistoryTable';
import { validateSimulationId } from '../domain/validators';
import { useReportQuery } from '../hooks/useReportQuery';
import { useReportStore } from '../store/reportStore';

export function ResultPage() {
  const navigate = useNavigate();
  const { simulationId } = useParams<{ simulationId: string }>();
  const routeError = validateSimulationId(simulationId);

  const { loadReport, refreshReport } = useReportQuery();
  const cacheBySimulationId = useReportStore((state) => state.cacheBySimulationId);
  const isLoading = useReportStore((state) => state.isLoading);
  const error = useReportStore((state) => state.error);

  useEffect(() => {
    if (!simulationId || routeError) {
      return;
    }
    void loadReport(simulationId);
  }, [simulationId, routeError, loadReport]);

  if (routeError) {
    return (
      <main>
        <p role="alert">{routeError}</p>
      </main>
    );
  }

  const entry = simulationId ? cacheBySimulationId[simulationId] : undefined;
  const report = entry?.report;

  return (
    <main>
      <h1>결과 조회</h1>

      {error && (
        <div role="alert" style={{ border: '1px solid #cc0000', padding: 8, marginBottom: 12 }}>
          <p>{error.messageKo}</p>
          {error.code === 'SIMULATION_NOT_FOUND' && (
            <button type="button" onClick={() => navigate('/')}>
              시작 화면으로
            </button>
          )}
          <button type="button" onClick={() => simulationId && refreshReport(simulationId)}>
            재시도
          </button>
        </div>
      )}

      {!report && isLoading && <p>보고서를 불러오는 중입니다...</p>}

      {report && (
        <>
          <ProfitSummaryCard
            initialSeed={report.profitSummary.initialSeed}
            finalSeed={report.profitSummary.finalSeed}
            totalProfit={report.profitSummary.totalProfit}
            totalProfitRate={report.profitSummary.totalProfitRate}
          />

          <TradeHistoryTable rows={report.trades} loading={isLoading && !report} emptyText="거래 내역이 없습니다." />

          <ComprehensiveReportCard summary={report.summary} />

          <button type="button" onClick={() => simulationId && refreshReport(simulationId)}>
            새로고침
          </button>
        </>
      )}
    </main>
  );
}