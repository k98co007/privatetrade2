import React from 'react';

type Props = {
  value: string;
  error?: string;
  disabled?: boolean;
  onChange: (value: string) => void;
  onBlur: () => void;
};

export function SymbolInput({ value, error, disabled, onChange, onBlur }: Props) {
  return (
    <div>
      <label htmlFor="symbol-input">종목 심볼</label>
      <input
        id="symbol-input"
        value={value}
        disabled={disabled}
        aria-invalid={Boolean(error)}
        placeholder="005930.KS"
        onChange={(event) => onChange(event.target.value)}
        onBlur={onBlur}
      />
      {error && <p role="alert">{error}</p>}
    </div>
  );
}
