import React from 'react';

import type { ReportSummary } from '../domain/types';
import { formatCurrencyKRW, formatPercent } from '../utils/formatters';

type Props = {
  summary: ReportSummary;
};

export function ComprehensiveReportCard({ summary }: Props) {
  return (
    <section>
      <h2>종합 리포트</h2>
      <p>총 거래 수: {summary.totalTrades}</p>
      <p>수익 거래 수: {summary.profitTrades}</p>
      <p>손해 거래 수: {summary.lossTrades}</p>
      <p>보합 거래 수: {summary.flatTrades}</p>
      <p>미거래일: {summary.noTradeDays}</p>
      <p>수익 총액: {formatCurrencyKRW(summary.totalProfitAmount)}</p>
      <p>손해 총액: {formatCurrencyKRW(summary.totalLossAmount)}</p>
      <p>승률: {formatPercent(summary.winRate)}</p>
    </section>
  );
}
