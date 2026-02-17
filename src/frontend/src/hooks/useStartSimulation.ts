import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { normalizeStartResponse } from '../domain/normalizers';
import { toUiError } from '../domain/errorMapper';
import { normalizeSymbolInput, validateStartForm } from '../domain/validators';
import type { StrategyId } from '../domain/types';
import { startSimulation } from '../services/simulationApi';
import { useSimulationStore } from '../store/simulationStore';

type FieldErrors = {
  symbol?: string;
  symbols?: string;
  strategy?: string;
};

export function useStartSimulation() {
  const navigate = useNavigate();
  const createSimulation = useSimulationStore((state) => state.createSimulation);
  const updateStatus = useSimulationStore((state) => state.updateStatus);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [submitError, setSubmitError] = useState<string | null>(null);

  const submitStart = async (input: { symbol: string; symbols: string[]; strategy: StrategyId }): Promise<{ simulationId: string } | null> => {
    if (isSubmitting) {
      return null;
    }

    const normalizedSymbol = normalizeSymbolInput(input.symbol);
    const normalizedSymbols = input.symbols.map((value) => normalizeSymbolInput(value)).filter((value) => value.length > 0);
    const errors = validateStartForm(normalizedSymbol, input.strategy, normalizedSymbols);
    setFieldErrors(errors);
    setSubmitError(null);
    if (Object.keys(errors).length > 0) {
      return null;
    }

    setIsSubmitting(true);
    try {
      const isStrategyD = input.strategy === 'two_minute_multi_symbol_buy_trailing_then_sell_trailing';
      const payload = isStrategyD
        ? { strategy: input.strategy, symbols: normalizedSymbols }
        : { strategy: input.strategy, symbol: normalizedSymbol };
      const response = await startSimulation(payload);
      const normalized = normalizeStartResponse(response);
      const displaySymbol = isStrategyD ? normalizedSymbols[0] ?? '' : normalizedSymbol;
      createSimulation({
        simulationId: normalized.simulationId,
        symbol: displaySymbol,
        strategy: input.strategy,
      });
      updateStatus(normalized.simulationId, 'running');
      navigate(`/monitoring/${normalized.simulationId}`);
      return { simulationId: normalized.simulationId };
    } catch (error) {
      const uiError = toUiError(error);
      setSubmitError(uiError.messageKo);
      return null;
    } finally {
      setIsSubmitting(false);
    }
  };

  return {
    submitStart,
    isSubmitting,
    fieldErrors,
    setFieldErrors,
    submitError,
  };
}
