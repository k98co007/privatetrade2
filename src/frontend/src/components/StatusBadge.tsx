import React from 'react';

import type { SimulationStatus } from '../domain/types';

type Props = {
  status: SimulationStatus;
  message?: string;
};

const STATUS_TEXT: Record<SimulationStatus, string> = {
  idle: '대기',
  starting: '시작 중',
  running: '실행 중',
  completed: '완료',
  error: '오류',
};

export function StatusBadge({ status, message }: Props) {
  return (
    <div role="status" style={{ padding: 8, border: '1px solid #aaa', display: 'inline-block' }}>
      <strong>{STATUS_TEXT[status]}</strong>
      {message ? <span> - {message}</span> : null}
    </div>
  );
}
