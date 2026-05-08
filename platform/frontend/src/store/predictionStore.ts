import { create } from "zustand";
import type { MatchPrediction, Country } from "@/types";

interface PredictionState {
  predictions: MatchPrediction[];
  currentPrediction: MatchPrediction | null;
  homeTeam: Country | null;
  awayTeam: Country | null;
  isGenerating: boolean;
  isLoading: boolean;
  error: string | null;
  setPredictions: (predictions: MatchPrediction[]) => void;
  setCurrentPrediction: (prediction: MatchPrediction | null) => void;
  setHomeTeam: (team: Country | null) => void;
  setAwayTeam: (team: Country | null) => void;
  swapTeams: () => void;
  setGenerating: (generating: boolean) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

export const usePredictionStore = create<PredictionState>((set) => ({
  predictions: [], currentPrediction: null, homeTeam: null, awayTeam: null,
  isGenerating: false, isLoading: false, error: null,
  setPredictions: (predictions) => set({ predictions, isLoading: false, error: null }),
  setCurrentPrediction: (prediction) => set({ currentPrediction: prediction }),
  setHomeTeam: (team) => set({ homeTeam: team }),
  setAwayTeam: (team) => set({ awayTeam: team }),
  swapTeams: () => set((s) => ({ homeTeam: s.awayTeam, awayTeam: s.homeTeam })),
  setGenerating: (generating) => set({ isGenerating: generating }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error, isLoading: false }),
  reset: () => set({ predictions: [], currentPrediction: null, homeTeam: null, awayTeam: null, isGenerating: false, isLoading: false, error: null }),
}));
