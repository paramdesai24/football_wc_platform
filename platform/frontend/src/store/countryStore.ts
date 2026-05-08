import { create } from "zustand";
import type { CountryRanking } from "@/types";

interface CountryState {
  countries: CountryRanking[];
  selectedCountry: CountryRanking | null;
  sortField: keyof CountryRanking;
  sortDirection: "asc" | "desc";
  confederationFilter: string | null;
  isLoading: boolean;
  error: string | null;
  setCountries: (countries: CountryRanking[]) => void;
  selectCountry: (country: CountryRanking | null) => void;
  setSortField: (field: keyof CountryRanking) => void;
  toggleSortDirection: () => void;
  setConfederationFilter: (confederation: string | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

const initialState = {
  countries: [] as CountryRanking[],
  selectedCountry: null as CountryRanking | null,
  sortField: "eloRating" as keyof CountryRanking,
  sortDirection: "desc" as const,
  confederationFilter: null as string | null,
  isLoading: false,
  error: null as string | null,
};

export const useCountryStore = create<CountryState>((set) => ({
  ...initialState,
  setCountries: (countries) => set({ countries, isLoading: false, error: null }),
  selectCountry: (country) => set({ selectedCountry: country }),
  setSortField: (field) => set((s) => ({ sortField: field, sortDirection: s.sortField === field && s.sortDirection === "desc" ? "asc" : "desc" })),
  toggleSortDirection: () => set((s) => ({ sortDirection: s.sortDirection === "asc" ? "desc" : "asc" })),
  setConfederationFilter: (confederation) => set({ confederationFilter: confederation }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error, isLoading: false }),
  reset: () => set(initialState),
}));
