export interface TeamAnalyticsResponse {
  country_id: string;
  country_name: string;
  confederation: string;
  elo_rating: number;
  attack_rating: number;
  defense_rating: number;
  recent_form: number;
  squad_strength: number;
  momentum: number;
  consistency: number;
  rank: number;
  power_index?: number;
  power_rank?: number;
  overall_rank_score?: number;
  attack_breakdown?: {
    recency_attack: number;
    squad_attack: number;
    elo_component: number;
    form_component: number;
  };
  defense_breakdown?: {
    defensive_record: number;
    defender_quality: number;
    goalkeeper_quality: number;
    clean_sheet_component: number;
  };
}
