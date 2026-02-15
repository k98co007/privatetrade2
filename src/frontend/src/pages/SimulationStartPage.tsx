import React, { useMemo, useState } from 'react';

import { StrategySelector } from '../components/StrategySelector';
import { SymbolInput } from '../components/SymbolInput';
import { STRATEGY_OPTIONS } from '../domain/mappers';
import type { StrategyId } from '../domain/types';
import { normalizeSymbolInput } from '../domain/validators';
import { useStartSimulation } from '../hooks/useStartSimulation';

export function SimulationStartPage() {
  const [symbolInput, setSymbolInput] = useState('');
  const [strategy, setStrategy] = useState<StrategyId>('sell_trailing_stop');

  const { submitStart, isSubmitting, fieldErrors, setFieldErrors } = useStartSimulation();

  const normalizedSymbol = useMemo(() => normalizeSymbolInput(symbolInput), [symbolInput]);

  return (
    <main>
      <h1>시뮬레이션 시작</h1>
      <form
        onSubmit={async (event) => {
          event.preventDefault();
          await submitStart({ symbol: normalizedSymbol, strategy });
        }}
      >
        <SymbolInput
          value={symbolInput}
          error={fieldErrors.symbol}
          disabled={isSubmitting}
          onChange={(value) => setSymbolInput(value)}
          onBlur={() => {
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
      </form>
    </main>
  );
}
