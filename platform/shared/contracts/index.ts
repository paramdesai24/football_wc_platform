export interface ChemistryEngine {
  scoreLineup(a: string[], b: string[]): number;
}

export interface PredictionRequest {
  homeTeam: string;
  awayTeam: string;
  tournamentStage?: string;
  neutralVenue?: boolean;
}

export interface SimulationRequest {
  tournamentId: string;
  runs: number;
}
