import React from 'react';

import type { StrategyOption } from '../domain/types';

type Props = {
  value: string;
  options: StrategyOption[];
  error?: string;
  disabled?: boolean;
  onChange: (value: string) => void;
};

export function StrategySelector({ value, options, error, disabled, onChange }: Props) {
  return (
    <div>
      <label htmlFor="strategy-select">전략</label>
      <select id="strategy-select" value={value} disabled={disabled} onChange={(event) => onChange(event.target.value)}>
        {options.map((option) => (
          <option key={option.id} value={option.id}>
            {option.label}
          </option>
        ))}
      </select>
      {error && <p role="alert">{error}</p>}
    </div>
  );
}
