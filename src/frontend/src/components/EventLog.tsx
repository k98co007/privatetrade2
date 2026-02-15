import React, { useMemo, useRef, useState } from 'react';

import type { EventItem } from '../domain/types';
import { formatDateTime } from '../utils/formatters';

type Props = {
  items: EventItem[];
  maxItems?: number;
  onClear: () => void;
};

function label(eventType: EventItem['eventType']): string {
  if (eventType === 'trade') {
    return '거래';
  }
  if (eventType === 'progress') {
    return '진행';
  }
  if (eventType === 'heartbeat') {
    return '상태';
  }
  if (eventType === 'completed') {
    return '완료';
  }
  if (eventType === 'error') {
    return '오류';
  }
  return '시스템';
}

export function EventLog({ items, maxItems = 500, onClear }: Props) {
  const [autoScroll, setAutoScroll] = useState(true);
  const containerRef = useRef<HTMLDivElement | null>(null);

  const rows = useMemo(() => items.slice(-maxItems), [items, maxItems]);

  React.useEffect(() => {
    if (!autoScroll || !containerRef.current) {
      return;
    }
    containerRef.current.scrollTop = containerRef.current.scrollHeight;
  }, [rows, autoScroll]);

  return (
    <section>
      <div style={{ display: 'flex', gap: 8 }}>
        <button type="button" onClick={() => setAutoScroll((prev) => !prev)}>
          자동 스크롤: {autoScroll ? 'ON' : 'OFF'}
        </button>
        <button type="button" onClick={onClear}>
          로그 비우기
        </button>
      </div>
      <div ref={containerRef} style={{ maxHeight: 240, overflow: 'auto', border: '1px solid #ccc', marginTop: 8 }}>
        <ul>
          {rows.map((item) => (
            <li key={item.eventId}>
              [{label(item.eventType)}] {formatDateTime(item.eventTime)}
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
