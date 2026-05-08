export interface Country {
  id: string;
  name: string;
  code: string;
  confederation: string;
  eloRating: number;
  fifaRanking: number;
}

export interface Player {
  id: string;
  firstName: string;
  surname: string;
  countryCode: string;
  position: string;
  age: number;
  club: string;
  formScore: number;
}

export interface MatchPrediction {
  homeTeamId: string;
  awayTeamId: string;
  predictedHomeGoals: number;
  predictedAwayGoals: number;
  homeWinProbability: number;
  drawProbability: number;
  awayWinProbability: number;
  confidence: number;
}

export interface SimulationConfig {
  iterations: number;
  model: "elo_poisson" | "xgboost" | "hybrid";
}

export interface ApiResponse<T> {
  data: T;
  status: "success" | "error";
  message?: string;
  timestamp: string;
}
