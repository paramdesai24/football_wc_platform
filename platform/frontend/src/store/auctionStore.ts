import { create } from "zustand";

export interface AuctionPlayer {
  id: string;
  name: string;
  position: string;
  tier: string;
  base_price: number;
  market_value: number;
  flag_code: string;
  image_url: string;
  club: string;
  goals_2526: number;
  assists_2526: number;
  minutes_2526: number;
  form_score: number;
}

export interface RoomUser {
  username: string;
  budget_left: number;
  squad_size: number;
  squad?: Array<{
    id: string;
    position: string;
    purchase_price?: number;
  }>;
  squad_details?: Array<{
    id: string;
    name: string;
    position: string;
    flag_code: string;
    club: string;
    purchase_price: number;
  }>;
}

interface UpcomingPlayer {
  name: string;
  position: string;
  tier: string;
  flag_code: string;
}

interface AuctionState {
  leagueId: string | null;
  userId: string | null;
  username: string | null;
  status: string;
  connectionStatus: 'connected' | 'disconnected' | 'reconnecting';
  currentPlayer: AuctionPlayer | null;
  currentHighBid: number;
  currentBidderId: string | null;
  currentNominator: string | null;
  users: Record<string, RoomUser>;
  upcomingPlayers: UpcomingPlayer[];
  myBudget: number;
  timerSeconds: number;
  maxTimerSeconds: number;
  bidPending: boolean;
  messages: string[];

  setLeague: (id: string, userId: string, username: string) => void;
  applyServerState: (payload: any) => void;
  setCurrentPlayer: (player: AuctionPlayer | null) => void;
  setHighBid: (amount: number, bidderId: string | null) => void;
  setUpcoming: (players: UpcomingPlayer[]) => void;
  setTimer: (s: number) => void;
  setMaxTimer: (max: number) => void;
  setStatus: (status: string) => void;
  setConnectionStatus: (status: 'connected' | 'disconnected' | 'reconnecting') => void;
  setBidPending: (pending: boolean) => void;
  addMessage: (msg: string) => void;
  reset: () => void;
}

const initialState = {
  leagueId: null,
  userId: null,
  username: null,
  status: "waiting",
  connectionStatus: "disconnected",
  currentPlayer: null,
  currentHighBid: 0,
  currentBidderId: null,
  currentNominator: null,
  users: {},
  upcomingPlayers: [],
  myBudget: 50000,
  timerSeconds: 30,
  maxTimerSeconds: 60,
  bidPending: false,
  messages: [],
};

export const useAuctionStore = create<AuctionState>((set, get) => ({
  ...initialState,

  setLeague: (id, userId, username) => set({ leagueId: id, userId, username }),

  applyServerState: (payload) =>
    set(() => {
      const existingUsers = get().users ?? {};
      const users = Object.fromEntries(
        Object.entries(payload.users ?? {}).map(([userId, user]: [string, any]) => [
          userId,
          {
            ...user,
            squad: user?.squad ?? existingUsers[userId]?.squad ?? [],
            squad_details: user?.squad_details ?? existingUsers[userId]?.squad_details ?? [],
          },
        ]),
      );

      return {
        status: payload.status,
        currentPlayer: payload.current_player,
        currentHighBid: payload.current_high_bid ?? 0,
        currentBidderId: payload.current_bidder_id ?? null,
        currentNominator: payload.current_nominator ?? null,
        users,
        myBudget: users?.[get().userId ?? ""]?.budget_left ?? get().myBudget,
      };
    }),

  setCurrentPlayer: (player) => set({ currentPlayer: player }),
  setHighBid: (amount, bidderId) => set({ currentHighBid: amount, currentBidderId: bidderId }),
  setUpcoming: (players) => set({ upcomingPlayers: players }),
  setTimer: (s) => set({ timerSeconds: s }),
  setMaxTimer: (max) => set({ maxTimerSeconds: max }),
  setStatus: (status) => set({ status }),
  setConnectionStatus: (connectionStatus) => set({ connectionStatus }),
  setBidPending: (bidPending) => set({ bidPending }),
  addMessage: (msg) => set((state) => ({ messages: [msg, ...state.messages].slice(0, 50) })),
  reset: () => set(initialState),
}));