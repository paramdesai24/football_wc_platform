export interface SimulationChampionRow {
  rank: number;
  team: string;
  country_name: string;
  win_pct: number;
  wins: number;
}

export interface SimulationResponse {
  iterations: number;
  results: SimulationChampionRow[];
  total_teams: number;
  statistics?: Record<string, unknown>;
  note?: string;
  error?: string;
}

export interface SimulationRequestPayload {
  iterations: number;
  model?: string;
  fixed_results?: Record<string, unknown>;
}
