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
  'two_minute_multi_symbol_buy_trailing_then_sell_trailing',
];

const STRATEGY_D_ID = 'two_minute_multi_symbol_buy_trailing_then_sell_trailing';
const STRATEGY_D_MAX_SYMBOLS = 20;

export function normalizeSymbolInput(raw: string): string {
  return raw.trim().toUpperCase();
}

export function normalizeSymbolsInput(raw: string): string {
  return raw
    .split(',')
    .map((value) => value.trim().toUpperCase())
    .filter((value) => value.length > 0)
    .join(', ');
}

export function parseSymbolsInput(raw: string): string[] {
  return raw
    .split(',')
    .map((value) => value.trim().toUpperCase())
    .filter((value) => value.length > 0);
}

export function validateSymbol(symbol: string): string | null {
  return SYMBOL_REGEX.test(symbol) ? null : '유효한 코스피 심볼을 입력하세요. 예: 005930.KS';
}

export function validateSymbols(symbols: string[]): string | null {
  if (symbols.length < 1 || symbols.length > STRATEGY_D_MAX_SYMBOLS) {
    return '종목 심볼을 1~20개 입력하세요. 예: 005930.KS, 000660.KS';
  }

  for (const symbol of symbols) {
    if (!SYMBOL_REGEX.test(symbol)) {
      return '유효한 코스피 심볼 목록을 입력하세요. 예: 005930.KS, 000660.KS';
    }
  }

  return null;
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

export function validateStartForm(
  symbol: string,
  strategy: string,
  symbols: string[] = [],
): { symbol?: string; symbols?: string; strategy?: string } {
  const symbolError = strategy === STRATEGY_D_ID ? null : validateSymbol(symbol);
  const symbolsError = strategy === STRATEGY_D_ID ? validateSymbols(symbols) : null;
  const strategyError = validateStrategy(strategy);
  return {
    ...(symbolError ? { symbol: symbolError } : {}),
    ...(symbolsError ? { symbols: symbolsError } : {}),
    ...(strategyError ? { strategy: strategyError } : {}),
  };
}
