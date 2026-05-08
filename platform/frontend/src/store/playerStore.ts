import { create } from "zustand";
import type { Player, PlayerPosition } from "@/types";

interface PlayerState {
  players: Player[];
  selectedPlayer: Player | null;
  positionFilter: PlayerPosition | null;
  countryFilter: string | null;
  searchQuery: string;
  sortField: keyof Player;
  sortDirection: "asc" | "desc";
  isLoading: boolean;
  error: string | null;
  setPlayers: (players: Player[]) => void;
  selectPlayer: (player: Player | null) => void;
  setPositionFilter: (position: PlayerPosition | null) => void;
  setCountryFilter: (country: string | null) => void;
  setSearchQuery: (query: string) => void;
  setSortField: (field: keyof Player) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

export const usePlayerStore = create<PlayerState>((set) => ({
  players: [], selectedPlayer: null, positionFilter: null, countryFilter: null,
  searchQuery: "", sortField: "formScore" as keyof Player, sortDirection: "desc" as const,
  isLoading: false, error: null,
  setPlayers: (players) => set({ players, isLoading: false, error: null }),
  selectPlayer: (player) => set({ selectedPlayer: player }),
  setPositionFilter: (position) => set({ positionFilter: position }),
  setCountryFilter: (country) => set({ countryFilter: country }),
  setSearchQuery: (query) => set({ searchQuery: query }),
  setSortField: (field) => set((s) => ({ sortField: field, sortDirection: s.sortField === field && s.sortDirection === "desc" ? "asc" : "desc" })),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error, isLoading: false }),
  reset: () => set({ players: [], selectedPlayer: null, positionFilter: null, countryFilter: null, searchQuery: "", sortField: "formScore", sortDirection: "desc", isLoading: false, error: null }),
}));
