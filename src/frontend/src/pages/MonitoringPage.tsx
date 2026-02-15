import React from 'react';
import { useParams } from 'react-router-dom';

import { EventLog } from '../components/EventLog';
import { ProgressBar } from '../components/ProgressBar';
import { StatusBadge } from '../components/StatusBadge';
import { validateSimulationId } from '../domain/validators';
import { useMonitoringSse } from '../hooks/useMonitoringSse';
import { useSimulationById, useSimulationEvents } from '../store/selectors';
import { useSimulationStore } from '../store/simulationStore';

export function MonitoringPage() {
  const { simulationId } = useParams<{ simulationId: string }>();
  const routeError = validateSimulationId(simulationId);

  const simulation = useSimulationById(simulationId);
  const events = useSimulationEvents(simulationId);
  const clearEvents = useSimulationStore((state) => state.clearEvents);

  const { isSseConnected, reconnectCount, reconnect } = useMonitoringSse(simulationId);

  if (routeError) {
    return (
      <main>
        <p role="alert">{routeError}</p>
      </main>
    );
  }

  if (!simulation) {
    return (
      <main>
        <h1>모니터링</h1>
        <p>시뮬레이션 정보를 찾는 중입니다...</p>
      </main>
    );
  }

  return (
    <main>
      <h1>실시간 모니터링</h1>
      <StatusBadge
        status={simulation.status}
        message={
          simulation.status === 'error'
            ? simulation.error?.messageKo
            : isSseConnected
              ? '연결됨'
              : `재연결 중 (${reconnectCount}/5)`
        }
      />

      <ProgressBar
        currentDay={simulation.progress.currentDay}
        totalDays={simulation.progress.totalDays}
        progressPct={simulation.progress.progressPct}
        tradingDate={simulation.progress.tradingDate}
      />

      {simulation.status === 'error' && (
        <button type="button" onClick={reconnect}>
          다시 연결
        </button>
      )}

      <EventLog items={events} onClear={() => simulationId && clearEvents(simulationId)} />
    </main>
  );
}
