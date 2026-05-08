export interface Country {
  id: string;
  name: string;
  code: string;
  confederation: Confederation;
  eloRating: number;
  fifaRanking: number;
  flagEmoji: string;
}

export interface CountryRanking extends Country {
  attackRating: number;
  defenseRating: number;
  formScore: number;
  recentForm: MatchResult[];
  trend: "up" | "down" | "stable";
  trendDelta: number;
}

export interface Player {
  id: string;
  firstName: string;
  surname: string;
  countryCode: string;
  countryName: string;
  position: PlayerPosition;
  age: number;
  club: string;
  marketValue: number;
  formScore: number;
  goalsScored: number;
  assists: number;
  appearances: number;
  minutesPlayed: number;
  metrics: PlayerMetrics;
}

export interface PlayerMetrics {
  attackContribution: number;
  defenseContribution: number;
  consistency: number;
  bigGamePerformance: number;
  internationalExperience: number;
}

export interface MatchPrediction {
  id: string;
  homeTeam: Country;
  awayTeam: Country;
  predictedHomeGoals: number;
  predictedAwayGoals: number;
  homeWinProbability: number;
  drawProbability: number;
  awayWinProbability: number;
  confidence: number;
  matchDate: string;
  venue: string;
  stage: TournamentStage;
}

export interface SimulationResult {
  id: string;
  iterations: number;
  champion: CountryProbability;
  finalist: CountryProbability[];
  semifinalists: CountryProbability[];
  quarterfinalists: CountryProbability[];
  groupStageResults: GroupResult[];
  timestamp: string;
}

export interface CountryProbability {
  country: Country;
  probability: number;
}

export interface GroupResult {
  groupName: string;
  standings: GroupStanding[];
}

export interface GroupStanding {
  position: number;
  country: Country;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  goalsFor: number;
  goalsAgainst: number;
  goalDifference: number;
  points: number;
  qualified: boolean;
}

export interface TeamAnalytics {
  country: Country;
  squad: Player[];
  squadStrength: number;
  averageAge: number;
  totalMarketValue: number;
  formTrend: number[];
  strengthByPosition: PositionStrength;
  recentMatches: MatchResult[];
}

export interface PositionStrength {
  goalkeeper: number;
  defense: number;
  midfield: number;
  attack: number;
}

export interface MatchResult {
  homeTeam: string;
  awayTeam: string;
  homeGoals: number;
  awayGoals: number;
  date: string;
  competition: string;
  result: "W" | "D" | "L";
}

export type PlayerPosition = "GK" | "DEF" | "MID" | "FWD";
export type Confederation = "UEFA" | "CONMEBOL" | "CONCACAF" | "CAF" | "AFC" | "OFC";
export type TournamentStage = "group" | "round-of-32" | "round-of-16" | "quarter-final" | "semi-final" | "third-place" | "final";

export interface NavigationItem {
  label: string;
  path: string;
}

export interface ApiResponse<T> {
  data: T;
  status: "success" | "error";
  message?: string;
  timestamp: string;
}

export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  page: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
}
