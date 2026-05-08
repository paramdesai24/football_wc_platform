export const ROUTES = {
  HOME: "/",
  COUNTRY_RANKINGS: "/country-rankings",
  MATCH_PREDICTOR: "/match-predictor",
  TOURNAMENT_SIMULATOR: "/tournament-simulator",
  PLAYER_ANALYTICS: "/player-analytics",
  TEAM_ANALYTICS: "/team-analytics",
  PREDICTIONS: "/predictions",
  NOT_FOUND: "*",
} as const;

export const NAV_ITEMS = [
  { label: "Dashboard", path: ROUTES.HOME },
  { label: "Country Rankings", path: ROUTES.COUNTRY_RANKINGS },
  { label: "Match Predictor", path: ROUTES.MATCH_PREDICTOR },
  { label: "Tournament Simulator", path: ROUTES.TOURNAMENT_SIMULATOR },
  { label: "Player Analytics", path: ROUTES.PLAYER_ANALYTICS },
  { label: "Team Analytics", path: ROUTES.TEAM_ANALYTICS },
  { label: "Predictions", path: ROUTES.PREDICTIONS },
] as const;
