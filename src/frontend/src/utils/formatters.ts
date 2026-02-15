export function formatCurrencyKRW(value: number): string {
  const integer = Math.trunc(value);
  const formatted = new Intl.NumberFormat('ko-KR').format(Math.abs(integer));
  return `${integer < 0 ? '-' : ''}${formatted}원`;
}

export function formatPercent(value: number): string {
  return `${value.toFixed(2)}%`;
}

export function formatDateTime(value: string | null): string {
  if (!value) {
    return '-';
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString('ko-KR', { hour12: false });
}
