import React, { useMemo, useState } from 'react';

import type { TradeRow } from '../domain/types';
import { formatCurrencyKRW, formatDateTime, formatPercent } from '../utils/formatters';

type SortOrder = 'asc' | 'desc';

type Props = {
  rows: TradeRow[];
  loading: boolean;
  emptyText: string;
};

export function TradeHistoryTable({ rows, loading, emptyText }: Props) {
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');

  const sortedRows = useMemo(() => {
    const copy = [...rows];
    copy.sort((a, b) => {
      if (!a.buyDatetime && !b.buyDatetime) {
        return a.tradeId - b.tradeId;
      }
      if (!a.buyDatetime) {
        return 1;
      }
      if (!b.buyDatetime) {
        return -1;
      }
      return sortOrder === 'asc' ? a.buyDatetime.localeCompare(b.buyDatetime) : b.buyDatetime.localeCompare(a.buyDatetime);
    });
    return copy;
  }, [rows, sortOrder]);

  if (loading) {
    return <p>거래내역을 불러오는 중입니다...</p>;
  }

  if (sortedRows.length === 0) {
    return <p>{emptyText}</p>;
  }

  return (
    <section>
      <h2>거래 내역</h2>
      <button type="button" onClick={() => setSortOrder((prev) => (prev === 'asc' ? 'desc' : 'asc'))}>
        정렬: {sortOrder}
      </button>
      <div style={{ overflowX: 'auto' }}>
        <table>
          <thead>
            <tr>
              <th>거래번호</th>
              <th>거래일</th>
              <th>매수일시</th>
              <th>매수가</th>
              <th>매수수량</th>
              <th>매수금액</th>
              <th>매도일시</th>
              <th>매도가</th>
              <th>매도수량</th>
              <th>매도금액</th>
              <th>매도사유</th>
              <th>세금</th>
              <th>수수료</th>
              <th>순손익</th>
              <th>수익률</th>
            </tr>
          </thead>
          <tbody>
            {sortedRows.map((row) => (
              <tr key={row.tradeId}>
                <td>{row.tradeId}</td>
                <td>{row.tradeDate}</td>
                <td>{formatDateTime(row.buyDatetime)}</td>
                <td>{row.buyPrice == null ? '-' : formatCurrencyKRW(row.buyPrice)}</td>
                <td>{row.buyQuantity}</td>
                <td>{formatCurrencyKRW(row.buyAmount)}</td>
                <td>{formatDateTime(row.sellDatetime)}</td>
                <td>{row.sellPrice == null ? '-' : formatCurrencyKRW(row.sellPrice)}</td>
                <td>{row.sellQuantity}</td>
                <td>{formatCurrencyKRW(row.sellAmount)}</td>
                <td>{row.sellReasonDisplay}</td>
                <td>{formatCurrencyKRW(row.tax)}</td>
                <td>{formatCurrencyKRW(row.fee)}</td>
                <td>{formatCurrencyKRW(row.netProfit)}</td>
                <td>{formatPercent(row.profitRate)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
