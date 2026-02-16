import type { StrategyId } from './types';

const SYMBOL_REGEX = /^[0-9]{6}\.KS$/;
const SIMULATION_ID_REGEX = /^[A-Za-z0-9:_-]{1,64}$/;
const ALLOWED_STRATEGIES: StrategyId[] = [
  'sell_trailing_stop',
  'buy_sell_trailing_stop',
  'rsi_buy_sell_trailing_stop',
  'rsi_only_trailing_stop',
  'buy_trailing_then_sell_trailing',
  'three_minute_buy_trailing_then_sell_trailing',
];

export function normalizeSymbolInput(raw: string): string {
  return raw.trim().toUpperCase();
}

export function validateSymbol(symbol: string): string | null {
  return SYMBOL_REGEX.test(symbol) ? null : '유효한 코스피 심볼을 입력하세요. 예: 005930.KS';
}

export function validateStrategy(strategy: string): string | null {
  return ALLOWED_STRATEGIES.includes(strategy as StrategyId)
    ? null
    : '전략 1/2/3/A/B/C 중 하나를 선택하세요.';
}

export function validateSimulationId(simulationId: string | undefined): string | null {
  if (!simulationId || !SIMULATION_ID_REGEX.test(simulationId)) {
    return '시뮬레이션 ID가 올바르지 않습니다.';
  }
  return null;
}

export function validateStartForm(symbol: string, strategy: string): { symbol?: string; strategy?: string } {
  const symbolError = validateSymbol(symbol);
  const strategyError = validateStrategy(strategy);
  return {
    ...(symbolError ? { symbol: symbolError } : {}),
    ...(strategyError ? { strategy: strategyError } : {}),
  };
}
