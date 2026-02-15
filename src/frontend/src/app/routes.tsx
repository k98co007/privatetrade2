import React from 'react';
import { createBrowserRouter, Outlet } from 'react-router-dom';

import { MonitoringPage } from '../pages/MonitoringPage';
import { ResultPage } from '../pages/ResultPage';
import { SimulationStartPage } from '../pages/SimulationStartPage';
import { useNetworkStatus } from '../hooks/useNetworkStatus';
import { useUiStore } from '../store/uiStore';

function AppLayout() {
  useNetworkStatus();
  const networkState = useUiStore((state) => state.networkState);

  return (
    <div style={{ maxWidth: 1280, margin: '0 auto', padding: 16 }}>
      {networkState !== 'online' && (
        <div role="status" style={{ marginBottom: 12, padding: 8, border: '1px solid #aaa' }}>
          네트워크 상태: {networkState === 'degraded' ? '재연결 중' : '오프라인'}
        </div>
      )}
      <Outlet />
    </div>
  );
}

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <SimulationStartPage /> },
      { path: 'monitoring/:simulationId', element: <MonitoringPage /> },
      { path: 'results/:simulationId', element: <ResultPage /> },
    ],
  },
]);
