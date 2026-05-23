import type { CountryRankingRow, PredictionHistoryRow, UpcomingPredictionRow } from "@/contracts";
import { MOCK_COUNTRY_RANKINGS, MOCK_PREDICTION_HISTORY, MOCK_UPCOMING_PREDICTIONS } from "./mockData";

export function getMockCountryRankings(): CountryRankingRow[] {
  return MOCK_COUNTRY_RANKINGS;
}

export function getMockPredictionHistory(): PredictionHistoryRow[] {
  return MOCK_PREDICTION_HISTORY;
}

export function getMockUpcomingPredictions(): UpcomingPredictionRow[] {
  return MOCK_UPCOMING_PREDICTIONS;
}
