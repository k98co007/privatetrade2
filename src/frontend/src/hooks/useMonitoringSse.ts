import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { toUiError } from '../domain/errorMapper';
import { normalizeEventItem, normalizeProgressPayload } from '../domain/normalizers';
import { open } from '../services/sseClient';
import type { SimulationStore } from '../store/simulationStore';
import { useSimulationStore } from '../store/simulationStore';
import type { UiStore } from '../store/uiStore';
import { useUiStore } from '../store/uiStore';
import { getBackoffDelayMs } from '../utils/retry';

export function useMonitoringSse(simulationId: string | undefined) {
  const navigate = useNavigate();
  const sourceRef = useRef<{ close: () => void } | null>(null);
  const reconnectTimerRef = useRef<number | null>(null);

  const [isSseConnected, setIsSseConnected] = useState(false);
  const [reconnectCount, setReconnectCount] = useState(0);

  const applyProgress = useSimulationStore((state: SimulationStore) => state.applyProgress);
  const appendEvent = useSimulationStore((state: SimulationStore) => state.appendEvent);
  const updateStatus = useSimulationStore((state: SimulationStore) => state.updateStatus);
  const setError = useSimulationStore((state: SimulationStore) => state.setError);
  const markEventApplied = useSimulationStore((state: SimulationStore) => state.markEventApplied);

  const setNetworkState = useUiStore((state: UiStore) => state.setNetworkState);
  const setLastHeartbeat = useUiStore((state: UiStore) => state.setLastHeartbeat);
  const pushToast = useUiStore((state: UiStore) => state.pushToast);

  const disconnect = useCallback(() => {
    if (sourceRef.current) {
      sourceRef.current.close();
      sourceRef.current = null;
    }
    if (reconnectTimerRef.current) {
      window.clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    setIsSseConnected(false);
  }, []);

  const connect = useCallback(
    (attempt = 0) => {
      if (!simulationId) {
        return;
      }

      disconnect();
      const lastEventId = useSimulationStore.getState().byId[simulationId]?.lastAppliedEventId ?? 0;

      sourceRef.current = open({
        simulationId,
        lastEventId,
        handlers: {
          onEvent: (eventType, payload, eventId) => {
            const lastApplied = useSimulationStore.getState().byId[simulationId]?.lastAppliedEventId ?? 0;
            if (eventId > 0 && eventId <= lastApplied) {
              return;
            }

            setIsSseConnected(true);
            setNetworkState('online');

            if (eventType === 'progress') {
              if (payload.current_day == null || payload.total_days == null || payload.progress_pct == null) {
                pushToast('진행률 이벤트 형식이 올바르지 않아 무시했습니다.');
                return;
              }
              applyProgress(simulationId, normalizeProgressPayload(payload), eventId);
              return;
            }

            if (eventType === 'trade') {
              const tradeType = payload.trade_type ?? payload.type;
              const tradeDatetime = payload.trade_datetime ?? payload.datetime;
              const price = payload.price;
              const quantity = payload.quantity;
              if (tradeType == null || tradeDatetime == null || price == null || quantity == null) {
                pushToast('거래 이벤트 필수 값이 누락되어 무시했습니다.');
                return;
              }
              appendEvent(simulationId, normalizeEventItem(payload, eventType, eventId));
              return;
            }

            if (eventType === 'heartbeat') {
              const timestamp =
                (payload.timestamp as string | undefined) ??
                (payload.server_time as string | undefined) ??
                new Date().toISOString();
              setLastHeartbeat(timestamp);
              markEventApplied(simulationId, eventId);
              return;
            }

            if (eventType === 'completed') {
              updateStatus(simulationId, 'completed');
              markEventApplied(simulationId, eventId);
              disconnect();
              navigate(`/results/${simulationId}`);
              return;
            }

            if (eventType === 'error') {
              const uiError = toUiError({
                status: 500,
                code: payload.code,
                message: payload.message,
              });
              setError(simulationId, uiError);
            }

            appendEvent(simulationId, normalizeEventItem(payload, eventType, eventId));
          },
          onError: (error) => {
            disconnect();
            setNetworkState('degraded');
            setReconnectCount(attempt + 1);

            if (attempt >= 4) {
              updateStatus(simulationId, 'error');
              setError(simulationId, toUiError(error));
              return;
            }

            reconnectTimerRef.current = window.setTimeout(() => connect(attempt + 1), getBackoffDelayMs(attempt));
          },
        },
      });
    },
    [
      simulationId,
      disconnect,
      applyProgress,
      appendEvent,
      updateStatus,
      setError,
      markEventApplied,
      setNetworkState,
      setLastHeartbeat,
      pushToast,
      navigate,
    ],
  );

  useEffect(() => {
    if (!simulationId) {
      return;
    }
    connect(0);
    return disconnect;
  }, [simulationId, connect, disconnect]);

  const reconnect = useCallback(() => {
    setReconnectCount(0);
    connect(0);
  }, [connect]);

  return {
    isSseConnected,
    reconnectCount,
    reconnect,
    disconnect,
  };
}
