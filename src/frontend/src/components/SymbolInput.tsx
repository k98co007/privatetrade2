import React from 'react';

type Props = {
  value: string;
  error?: string;
  disabled?: boolean;
  label?: string;
  placeholder?: string;
  onChange: (value: string) => void;
  onBlur: () => void;
};

export function SymbolInput({ value, error, disabled, label = '종목 심볼', placeholder = '005930.KS', onChange, onBlur }: Props) {
  return (
    <div>
      <label htmlFor="symbol-input">{label}</label>
      <input
        id="symbol-input"
        value={value}
        disabled={disabled}
        aria-invalid={Boolean(error)}
        placeholder={placeholder}
        onChange={(event) => onChange(event.target.value)}
        onBlur={onBlur}
      />
      {error && <p role="alert">{error}</p>}
    </div>
  );
}
