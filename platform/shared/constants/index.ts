export const CONFEDERATIONS = ["UEFA", "CONMEBOL", "CONCACAF", "CAF", "AFC", "OFC"] as const;

export const POSITIONS = ["GK", "DEF", "MID", "FWD"] as const;

export const TOURNAMENT_STAGES = [
  "group",
  "round-of-32",
  "round-of-16",
  "quarter-final",
  "semi-final",
  "third-place",
  "final",
] as const;

export const WC_2026 = {
  name: "FIFA World Cup 2026™",
  year: 2026,
  hosts: ["United States", "Mexico", "Canada"],
  teams: 48,
  groups: 12,
  teamsPerGroup: 4,
  totalMatches: 104,
  venues: 16,
  startDate: "2026-06-11",
  endDate: "2026-07-19",
} as const;

export const API_ENDPOINTS = {
  HEALTH: "/health",
  COUNTRIES: "/countries",
  PLAYERS: "/players",
  PREDICTIONS: "/predictions",
  SIMULATION: "/simulation",
  ANALYTICS: "/analytics",
} as const;

export const FORM_THRESHOLDS = {
  EXCELLENT: 85,
  GOOD: 70,
  AVERAGE: 50,
  POOR: 30,
} as const;

export const ELO_CONFIG = {
  INITIAL_RATING: 1500,
  K_FACTOR: 40,
  HOME_ADVANTAGE: 100,
  DECAY_FACTOR: 0.98,
} as const;
