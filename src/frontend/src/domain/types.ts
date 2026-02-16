export type SimulationStatus = 'idle' | 'starting' | 'running' | 'completed' | 'error';
export type NetworkState = 'online' | 'offline' | 'degraded';

export type StrategyId =
  | 'sell_trailing_stop'
  | 'buy_sell_trailing_stop'
  | 'rsi_buy_sell_trailing_stop'
  | 'rsi_only_trailing_stop'
  | 'buy_trailing_then_sell_trailing'
  | 'three_minute_buy_trailing_then_sell_trailing';

export type StrategyOption = {
  id: StrategyId;
  label: string;
};

export type UiError = {
  code: string;
  messageKo: string;
  requestId?: string;
  recoverable: boolean;
};

export type SimulationMeta = {
  simulationId: string;
  symbol: string;
  strategy: StrategyId;
};

export type ProgressState = {
  currentDay: number;
  totalDays: number;
  progressPct: number;
  tradingDate: string | null;
};

export type EventType = 'progress' | 'trade' | 'heartbeat' | 'completed' | 'error' | 'warning';

export type EventItem = {
  eventId: number;
  eventType: EventType;
  eventTime: string;
  payload: Record<string, unknown>;
};

export type ProfitSummary = {
  initialSeed: number;
  finalSeed: number;
  totalProfit: number;
  totalProfitRate: number;
};

export type ReportSummary = {
  totalTrades: number;
  profitTrades: number;
  lossTrades: number;
  flatTrades: number;
  noTradeDays: number;
  totalProfitAmount: number;
  totalLossAmount: number;
  winRate: number;
};

export type TradeRow = {
  tradeId: number;
  tradeDate: string;
  buyDatetime: string | null;
  buyPrice: number | null;
  buyQuantity: number;
  buyAmount: number;
  sellDatetime: string | null;
  sellPrice: number | null;
  sellQuantity: number;
  sellAmount: number;
  sellReason: string;
  sellReasonDisplay: string;
  tax: number;
  fee: number;
  netProfit: number;
  profitRate: number;
};

export type ComprehensiveReport = {
  schemaVersion: string;
  simulationId: string;
  symbol: string;
  strategy: string;
  period: {
    start_date: string;
    end_date: string;
  };
  profitSummary: ProfitSummary;
  summary: ReportSummary;
  trades: TradeRow[];
};

export type ReportCacheEntry = {
  simulationId: string;
  schemaVersion: string;
  fetchedAt: number;
  report: ComprehensiveReport;
};

export type StartSimulationPayload = {
  symbol: string;
  strategy: StrategyId;
};

export type StartSimulationResponse = {
  simulation_id: string;
  status: 'queued' | 'running' | 'completed' | 'error';
  symbol: string;
  strategy: StrategyId;
  created_at: string;
  updated_at: string;
};

export type ApiEnvelope<T> = {
  success: boolean;
  data: T;
  error?: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
  meta?: {
    request_id: string;
    timestamp: string;
  };
};

export type ApiReportResponse = {
  schema_version: string;
  simulation_id: string;
  symbol: string;
  strategy: string;
  period: {
    start_date: string;
    end_date: string;
  };
  profit_summary: {
    initial_seed: string;
    final_seed: string;
    total_profit: string;
    total_profit_rate: string;
  };
  summary: {
    total_trades: number;
    profit_trades: number;
    loss_trades: number;
    flat_trades: number;
    no_trade_days: number;
    total_profit_amount: string;
    total_loss_amount: string;
    win_rate: string;
  };
  trades: Array<{
    trade_id: number;
    trade_date: string;
    buy_datetime: string | null;
    buy_price: string | null;
    buy_quantity: number;
    buy_amount: string;
    sell_datetime: string | null;
    sell_price: string | null;
    sell_quantity: number;
    sell_amount: string;
    sell_reason: string;
    sell_reason_display: string;
    tax: string;
    fee: string;
    net_profit: string;
    profit_rate: string;
    seed_money_after: string;
  }>;
};
