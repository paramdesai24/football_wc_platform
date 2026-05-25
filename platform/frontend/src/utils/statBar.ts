export function smartScoreBar(elo: number): number {
  const min = 1600;
  const max = 2200;
  return Math.min(100, Math.max(0, ((elo - min) / (max - min)) * 100));
}

export function ratingBar(value: number): number {
  return Math.min(100, Math.max(0, value));
}

export function formBar(value: number): number {
  return Math.min(100, Math.max(0, value * 100));
}

export function momentumBar(value: number): number {
  return Math.min(100, Math.max(0, ((value + 1) / 2) * 100));
}

export function consistencyBar(value: number): number {
  return Math.min(100, Math.max(0, value * 100));
}