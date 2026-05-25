export const ROUTES = {
  HOME: "/",
  PREDICTIONS: "/predictions",
  RANKINGS: "/rankings",
  TEAM_ANALYTICS: "/analytics",
  TOURNAMENT_SIMULATOR: "/tournament",
  PLAY_AS_TEAM: "/play-as-team",
  ABOUT: "/about",
  NOT_FOUND: "*",
} as const;

/** Sidebar nav — mirrors the Streamlit sidebar exactly */
export const NAV_ITEMS = [
  { label: "Dashboard", path: ROUTES.HOME, icon: "dashboard" },
  { label: "Predictions", path: ROUTES.PREDICTIONS, icon: "target" },
  { label: "Rankings", path: ROUTES.RANKINGS, icon: "leaderboard" },
  { label: "Analytics", path: ROUTES.TEAM_ANALYTICS, icon: "analytics" },
  { label: "Tournament", path: ROUTES.TOURNAMENT_SIMULATOR, icon: "emoji_events" },
  { label: "Play As A Team", path: ROUTES.PLAY_AS_TEAM, icon: "sports_esports" },
  { label: "About", path: ROUTES.ABOUT, icon: "info" },
] as const;
