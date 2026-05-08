export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

export function round(value: number, digits = 2): number {
  const factor = 10 ** digits;
  return Math.round(value * factor) / factor;
}

export function toPercent(value: number, digits = 1): string {
  return `${round(value * 100, digits)}%`;
}

export function isoNow(): string {
  return new Date().toISOString();
}
