export interface PredictionRequestPayload {
  home_team_id: string;
  away_team_id: string;
  venue?: string;
  tournament?: string;
}

export interface PredictionResponse {
  match?: string;
  home_win_pct?: number;
  draw_pct?: number;
  away_win_pct?: number;
  confidence?: number;
  predicted_score?: string;
  home_xg?: number;
  away_xg?: number;
  home_team?: string;
  away_team?: string;
  explanation?: string;
  error?: string;
}

export interface PredictionHistoryRow {
  timestamp?: string;
  match?: string;
  predicted_score?: string;
  confidence?: number;
  home_win_pct?: number;
  draw_pct?: number;
  away_win_pct?: number;
}

export interface UpcomingPredictionRow {
  match: string;
  home_win: string;
  draw: string;
  away_win: string;
}
