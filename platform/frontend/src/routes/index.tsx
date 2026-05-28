import { createBrowserRouter } from "react-router-dom";
import { AppLayout } from "@/layouts/AppLayout";
import { ROUTES } from "./constants";
import DashboardPage from "@/pages/DashboardPage";
import AuctionPage from "@/pages/AuctionPage";
import AuctionRoomPage from "@/pages/AuctionRoomPage";
import LeaguePage from "@/pages/LeaguePage";
import LeagueSquadPage from "@/pages/LeagueSquadPage";
import LeagueLeaderboardPage from "@/pages/LeagueLeaderboardPage";
import PredictionsPage from "@/pages/PredictionsPage";
import RankingsPage from "@/pages/RankingsPage";
import TeamAnalyticsPage from "@/pages/TeamAnalyticsPage";
import TournamentPage from "@/pages/TournamentPage";
import PlayAsTeamPage from "@/pages/PlayAsTeamPage";
import AboutPage from "@/pages/AboutPage";
import NotFoundPage from "@/pages/NotFoundPage";

export const router = createBrowserRouter([
  {
    element: <AppLayout />,
    children: [
      { path: ROUTES.HOME, element: <DashboardPage /> },
      { path: ROUTES.AUCTION, element: <AuctionPage /> },
      { path: "/auction/room/:id", element: <AuctionRoomPage /> },
      { path: "/league/:id", element: <LeaguePage /> },
      { path: "/league/:id/squad/:uid", element: <LeagueSquadPage /> },
      { path: "/league/:id/leaderboard", element: <LeagueLeaderboardPage /> },
      { path: ROUTES.PREDICTIONS, element: <PredictionsPage /> },
      { path: ROUTES.RANKINGS, element: <RankingsPage /> },
      { path: ROUTES.TEAM_ANALYTICS, element: <TeamAnalyticsPage /> },
      { path: ROUTES.TOURNAMENT_SIMULATOR, element: <TournamentPage /> },
      { path: ROUTES.PLAY_AS_TEAM, element: <PlayAsTeamPage /> },
      { path: ROUTES.ABOUT, element: <AboutPage /> },
      { path: ROUTES.NOT_FOUND, element: <NotFoundPage /> },
    ],
  },
]);
