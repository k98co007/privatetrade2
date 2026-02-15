import type { StrategyOption } from './types';

export const STRATEGY_OPTIONS: StrategyOption[] = [
  { id: 'sell_trailing_stop', label: '매도 트레일링 스탑' },
  { id: 'buy_sell_trailing_stop', label: '매수/매도 트레일링 스탑' },
  { id: 'rsi_buy_sell_trailing_stop', label: 'RSI 매수/매도 트레일링 스탑' },
];

const SELL_REASON_MAP: Record<string, string> = {
  take_profit: '익절',
  stop_loss: '손절',
  trailing_stop: '트레일링 스탑',
  no_trade: '미거래',
  error_skip: '오류 스킵',
};

export function mapSellReasonToKo(reason: string): string {
  return SELL_REASON_MAP[reason] ?? reason;
}
