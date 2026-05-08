import { create } from "zustand";
import type { SimulationResult } from "@/types";

interface SimulationState {
  results: SimulationResult | null;
  iterationCount: number;
  isRunning: boolean;
  progress: number;
  history: SimulationResult[];
  isLoading: boolean;
  error: string | null;
  setResults: (results: SimulationResult) => void;
  setIterationCount: (count: number) => void;
  setRunning: (running: boolean) => void;
  setProgress: (progress: number) => void;
  addToHistory: (result: SimulationResult) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

export const useSimulationStore = create<SimulationState>((set) => ({
  results: null, iterationCount: 10000, isRunning: false, progress: 0,
  history: [], isLoading: false, error: null,
  setResults: (results) => set({ results, isRunning: false, progress: 100, error: null }),
  setIterationCount: (count) => set({ iterationCount: count }),
  setRunning: (running) => set({ isRunning: running }),
  setProgress: (progress) => set({ progress }),
  addToHistory: (result) => set((s) => ({ history: [result, ...s.history].slice(0, 10) })),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error, isRunning: false }),
  reset: () => set({ results: null, iterationCount: 10000, isRunning: false, progress: 0, history: [], isLoading: false, error: null }),
}));
