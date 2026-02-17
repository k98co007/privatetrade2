import React, { useMemo, useState } from 'react';

import { StrategySelector } from '../components/StrategySelector';
import { SymbolInput } from '../components/SymbolInput';
import { STRATEGY_OPTIONS } from '../domain/mappers';
import type { StrategyId } from '../domain/types';
import { normalizeSymbolInput, normalizeSymbolsInput, parseSymbolsInput } from '../domain/validators';
import { useStartSimulation } from '../hooks/useStartSimulation';

export function SimulationStartPage() {
  const [symbolInput, setSymbolInput] = useState('');
  const [symbolsInput, setSymbolsInput] = useState('');
  const [strategy, setStrategy] = useState<StrategyId>('sell_trailing_stop');

  const { submitStart, isSubmitting, fieldErrors, setFieldErrors, submitError } = useStartSimulation();

  const normalizedSymbol = useMemo(() => normalizeSymbolInput(symbolInput), [symbolInput]);
  const normalizedSymbolsInput = useMemo(() => normalizeSymbolsInput(symbolsInput), [symbolsInput]);
  const normalizedSymbols = useMemo(() => parseSymbolsInput(symbolsInput), [symbolsInput]);
  const isStrategyD = strategy === 'two_minute_multi_symbol_buy_trailing_then_sell_trailing';

  return (
    <main>
      <h1>시뮬레이션 시작</h1>
      <form
        onSubmit={async (event) => {
          event.preventDefault();
          await submitStart({ symbol: normalizedSymbol, symbols: normalizedSymbols, strategy });
        }}
      >
        <SymbolInput
          value={isStrategyD ? symbolsInput : symbolInput}
          error={isStrategyD ? fieldErrors.symbols : fieldErrors.symbol}
          disabled={isSubmitting}
          label={isStrategyD ? '모니터링 종목 심볼 목록' : '종목 심볼'}
          placeholder={isStrategyD ? '005930.KS, 000660.KS' : '005930.KS'}
          onChange={(value) => {
            if (isStrategyD) {
              setSymbolsInput(value);
            } else {
              setSymbolInput(value);
            }
          }}
          onBlur={() => {
            if (isStrategyD) {
              setSymbolsInput(normalizedSymbolsInput);
              if (fieldErrors.symbols) {
                setFieldErrors((prev) => ({ ...prev, symbols: undefined }));
              }
              return;
            }

            setSymbolInput(normalizedSymbol);
            if (fieldErrors.symbol) {
              setFieldErrors((prev) => ({ ...prev, symbol: undefined }));
            }
          }}
        />
        <StrategySelector
          value={strategy}
          options={STRATEGY_OPTIONS}
          error={fieldErrors.strategy}
          disabled={isSubmitting}
          onChange={(value) => setStrategy(value as StrategyId)}
        />
        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? '시작 중...' : '시작'}
        </button>
        {submitError && <p role="alert">{submitError}</p>}
      </form>
    </main>
  );
}
