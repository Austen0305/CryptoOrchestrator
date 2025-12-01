import { create } from 'zustand';
import type { ScenarioResponse } from '@/lib/api';

type ScenarioState = {
  last: ScenarioResponse | null;
  history: ScenarioResponse[];
  add: (result: ScenarioResponse) => void;
  clear: () => void;
};

export const useScenarioStore = create<ScenarioState>((set) => ({
  last: null,
  history: [],
  add: (result) =>
    set((s) => {
      const next = [result, ...s.history].slice(0, 10);
      return { last: result, history: next };
    }),
  clear: () => set({ last: null, history: [] }),
}));
