import React from 'react';

import { formatCurrencyKRW, formatPercent } from '../utils/formatters';

type Props = {
  initialSeed: number;
  finalSeed: number;
  totalProfit: number;
  totalProfitRate: number;
};

export function ProfitSummaryCard({ initialSeed, finalSeed, totalProfit, totalProfitRate }: Props) {
  return (
    <section>
      <h2>수익 요약</h2>
      <p>초기 시드머니: {formatCurrencyKRW(initialSeed)}</p>
      <p>최종 시드머니: {formatCurrencyKRW(finalSeed)}</p>
      <p>총 수익금: {formatCurrencyKRW(totalProfit)}</p>
      <p>총 수익률: {formatPercent(totalProfitRate)}</p>
    </section>
  );
}
