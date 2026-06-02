import { createBrowserRouter } from "react-router-dom";
import { AppLayout } from "@/layouts/AppLayout";
import { ROUTES } from "./constants";
import DashboardPage from "@/pages/DashboardPage";
import AuctionLobbyPage from "@/pages/AuctionLobbyPage";
import AuctionRoomPage from "@/pages/AuctionRoomPage";
import AuthPage from "@/pages/AuthPage";
import LeaguePage from "@/pages/LeaguePage";
import SquadPage from "@/pages/SquadPage";
import LeaderboardPage from "@/pages/LeaderboardPage";
import PredictionsPage from "@/pages/PredictionsPage";
import RankingsPage from "@/pages/RankingsPage";
import TeamAnalyticsPage from "@/pages/TeamAnalyticsPage";
import TournamentPage from "@/pages/TournamentPage";
import PlayAsTeamPage from "@/pages/PlayAsTeamPage";
import AboutPage from "@/pages/AboutPage";
import AdminMatchPage from "@/pages/AdminMatchPage";
import AuctionInfoPage from "@/pages/AuctionInfoPage";
import NotFoundPage from "@/pages/NotFoundPage";
import AuthGuard from '@/components/layout/AuthGuard'

export const router = createBrowserRouter([
  {
    element: <AppLayout />,
    children: [
      { path: ROUTES.HOME, element: <DashboardPage /> },
      { path: '/auth', element: <AuthPage /> },
      { path: ROUTES.AUCTION, element: <AuthGuard><AuctionLobbyPage /></AuthGuard> },
      { path: "/auction/room/:id", element: <AuthGuard><AuctionRoomPage /></AuthGuard> },
      { path: "/auction/info", element: <AuthGuard><AuctionInfoPage /></AuthGuard> },
      { path: "/league/:id", element: <LeaguePage /> },
      { path: "/league/:id/squad/:uid", element: <AuthGuard><SquadPage /></AuthGuard> },
      { path: "/league/:id/leaderboard", element: <AuthGuard><LeaderboardPage /></AuthGuard> },
      { path: ROUTES.PREDICTIONS, element: <PredictionsPage /> },
      { path: ROUTES.RANKINGS, element: <RankingsPage /> },
      { path: ROUTES.TEAM_ANALYTICS, element: <TeamAnalyticsPage /> },
      { path: ROUTES.TOURNAMENT_SIMULATOR, element: <TournamentPage /> },
      { path: ROUTES.PLAY_AS_TEAM, element: <PlayAsTeamPage /> },
      { path: ROUTES.ABOUT, element: <AboutPage /> },
      { path: "/admin/match-entry", element: <AdminMatchPage /> },
      { path: ROUTES.NOT_FOUND, element: <NotFoundPage /> },
    ],
  },
]);
