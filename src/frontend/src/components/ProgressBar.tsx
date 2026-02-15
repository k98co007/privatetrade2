import React from 'react';

type Props = {
  currentDay: number;
  totalDays: number;
  progressPct: number;
  tradingDate: string | null;
};

export function ProgressBar({ currentDay, totalDays, progressPct, tradingDate }: Props) {
  return (
    <section aria-label="진행률">
      <p>
        {currentDay}/{totalDays}일 완료 ({progressPct.toFixed(2)}%)
      </p>
      <progress max={100} value={progressPct} style={{ width: '100%' }} />
      <p>거래일: {tradingDate ?? '-'}</p>
    </section>
  );
}
