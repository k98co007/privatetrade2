import { mapSellReasonToKo } from './mappers';
import type {
  ApiReportResponse,
  ComprehensiveReport,
  EventItem,
  EventType,
  ProgressState,
  StartSimulationResponse,
  TradeRow,
} from './types';

function toNumber(value: string | number | null | undefined): number {
  if (typeof value === 'number') {
    return Number.isFinite(value) ? value : 0;
  }
  if (typeof value === 'string' && value.length > 0) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : 0;
  }
  return 0;
}

export function normalizeStartResponse(response: StartSimulationResponse): { simulationId: string; status: string } {
  return {
    simulationId: response.simulation_id,
    status: response.status,
  };
}

export function normalizeProgressPayload(payload: Record<string, unknown>): ProgressState {
  return {
    currentDay: toNumber(payload.current_day as string | number),
    totalDays: Math.max(1, toNumber(payload.total_days as string | number)),
    progressPct: Math.min(100, Math.max(0, toNumber(payload.progress_pct as string | number))),
    tradingDate: (payload.trading_date as string | undefined) ?? null,
  };
}

export function normalizeEventItem(payload: Record<string, unknown>, eventType: EventType, eventId: number): EventItem {
  const eventTime =
    (payload.event_time as string | undefined) ??
    (payload.server_time as string | undefined) ??
    (payload.trade_datetime as string | undefined) ??
    new Date().toISOString();

  return {
    eventId,
    eventType,
    eventTime,
    payload,
  };
}

function normalizeTrades(rows: ApiReportResponse['trades']): TradeRow[] {
  const normalized = rows
    .filter((row) => row.trade_id != null)
    .map((row) => ({
      tradeId: row.trade_id,
      tradeDate: row.trade_date,
      symbolCode: row.symbol_code,
      buyDatetime: row.buy_datetime,
      buyPrice: row.buy_price === null ? null : toNumber(row.buy_price),
      buyQuantity: toNumber(row.buy_quantity),
      buyAmount: toNumber(row.buy_amount),
      sellDatetime: row.sell_datetime,
      sellPrice: row.sell_price === null ? null : toNumber(row.sell_price),
      sellQuantity: toNumber(row.sell_quantity),
      sellAmount: toNumber(row.sell_amount),
      sellReason: row.sell_reason,
      sellReasonDisplay: row.sell_reason_display || mapSellReasonToKo(row.sell_reason),
      tax: toNumber(row.tax),
      fee: toNumber(row.fee),
      netProfit: toNumber(row.net_profit),
      profitRate: toNumber(row.profit_rate),
    }));

  return normalized.sort((a, b) => {
    if (!a.buyDatetime && !b.buyDatetime) {
      return a.tradeId - b.tradeId;
    }
    if (!a.buyDatetime) {
      return 1;
    }
    if (!b.buyDatetime) {
      return -1;
    }
    return a.buyDatetime.localeCompare(b.buyDatetime);
  });
}

export function normalizeReport(response: ApiReportResponse): ComprehensiveReport {
  return {
    schemaVersion: response.schema_version,
    simulationId: response.simulation_id,
    symbol: response.symbol,
    strategy: response.strategy,
    period: response.period,
    profitSummary: {
      initialSeed: toNumber(response.profit_summary.initial_seed),
      finalSeed: toNumber(response.profit_summary.final_seed),
      totalProfit: toNumber(response.profit_summary.total_profit),
      totalProfitRate: toNumber(response.profit_summary.total_profit_rate),
    },
    summary: {
      totalTrades: response.summary.total_trades,
      profitTrades: response.summary.profit_trades,
      lossTrades: response.summary.loss_trades,
      flatTrades: response.summary.flat_trades,
      noTradeDays: response.summary.no_trade_days,
      totalProfitAmount: toNumber(response.summary.total_profit_amount),
      totalLossAmount: toNumber(response.summary.total_loss_amount),
      winRate: toNumber(response.summary.win_rate),
    },
    trades: normalizeTrades(response.trades),
  };
}
