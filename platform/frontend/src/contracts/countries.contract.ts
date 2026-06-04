export interface CountryRankingRow {
  rank: number;
  country_name: string;
  country_uid: string;
  elo_rating: number;
  attack_rating: number;
  defense_rating: number;
  recent_form_score?: number;
  squad_overall_strength?: number;
  momentum_score?: number;
  consistency_score?: number;
  overall_rank_score?: number;
  confederation?: string;
}

export interface CountryRankingsResponse {
  data: CountryRankingRow[];
  total: number;
  limit?: number;
  offset?: number;
}

export interface CountryResponse {
  data: CountryRankingRow | null;
}
