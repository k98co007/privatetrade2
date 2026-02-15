import type { EventType } from '../domain/types';

type OpenArgs = {
  simulationId: string;
  lastEventId?: number;
  handlers: {
    onEvent: (eventType: EventType, payload: Record<string, unknown>, eventId: number) => void;
    onError: (error: unknown) => void;
  };
};

export type EventSourceLike = {
  close: () => void;
};

const EVENT_TYPES: EventType[] = ['progress', 'trade', 'heartbeat', 'completed', 'error', 'warning'];

export function open({ simulationId, lastEventId, handlers }: OpenArgs): EventSourceLike {
  const encodedId = encodeURIComponent(simulationId);
  const query = typeof lastEventId === 'number' ? `?last_event_id=${lastEventId}` : '';
  const source = new EventSource(`/api/simulations/${encodedId}/stream${query}`);

  EVENT_TYPES.forEach((eventType) => {
    source.addEventListener(eventType, (event) => {
      const message = event as MessageEvent;
      const payload = JSON.parse(message.data) as Record<string, unknown>;
      const eventId = Number((message as MessageEvent).lastEventId || 0);
      handlers.onEvent(eventType, payload, Number.isFinite(eventId) ? eventId : 0);
    });
  });

  source.onerror = (error) => {
    handlers.onError(error);
  };

  return source;
}
