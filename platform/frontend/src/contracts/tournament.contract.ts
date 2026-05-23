export interface TournamentMatchResponse {
  match_id?: number;
  stage?: string;
  home_team?: string;
  away_team?: string;
  home_score?: number;
  away_score?: number;
  winner?: string;
  locked?: boolean;
  editable?: boolean;
  user_overridden?: boolean;
  extra_time?: boolean;
  penalties?: boolean;
  penalty_score?: string;
  timeline?: unknown[];
  momentum_summary?: string;
}

export interface TournamentStateResponse {
  champion?: string;
  runner_up?: string;
  third_place?: string;
  matches?: TournamentMatchResponse[];
  group_standings?: Record<string, Record<string, unknown>[]>;
  statistics?: Record<string, unknown>;
  note?: string;
  error?: string;
}

export interface PlayAsTeamResponse {
  summary?: {
    titles_won?: number;
    average_finish?: string;
    goals_scored?: number;
    average_goals_for?: number;
    goals_conceded?: number;
    average_goals_against?: number;
    et_frequency?: number;
    penalty_frequency?: number;
    elimination_distribution?: Record<string, number>;
  };
  journeys?: Array<Record<string, unknown>>;
}
