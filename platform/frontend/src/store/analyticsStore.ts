import { create } from "zustand";
import type { TeamAnalytics } from "@/types";

interface AnalyticsState {
  teamAnalytics: TeamAnalytics | null;
  comparisonTeams: TeamAnalytics[];
  activeMetric: string;
  isLoading: boolean;
  error: string | null;
  setTeamAnalytics: (analytics: TeamAnalytics) => void;
  addComparisonTeam: (team: TeamAnalytics) => void;
  removeComparisonTeam: (countryId: string) => void;
  setActiveMetric: (metric: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

export const useAnalyticsStore = create<AnalyticsState>((set) => ({
  teamAnalytics: null, comparisonTeams: [], activeMetric: "eloRating",
  isLoading: false, error: null,
  setTeamAnalytics: (analytics) => set({ teamAnalytics: analytics, isLoading: false, error: null }),
  addComparisonTeam: (team) => set((s) => {
    if (s.comparisonTeams.length >= 4 || s.comparisonTeams.some((t) => t.country.id === team.country.id)) return s;
    return { comparisonTeams: [...s.comparisonTeams, team] };
  }),
  removeComparisonTeam: (countryId) => set((s) => ({ comparisonTeams: s.comparisonTeams.filter((t) => t.country.id !== countryId) })),
  setActiveMetric: (metric) => set({ activeMetric: metric }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error, isLoading: false }),
  reset: () => set({ teamAnalytics: null, comparisonTeams: [], activeMetric: "eloRating", isLoading: false, error: null }),
}));
