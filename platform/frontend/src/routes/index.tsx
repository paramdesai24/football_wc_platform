import { createBrowserRouter } from "react-router-dom";
import { AppLayout } from "@/layouts/AppLayout";
import { HomePage } from "@/pages/HomePage";
import { RankingsPage } from "@/pages/RankingsPage";
import { PredictorPage } from "@/pages/PredictorPage";
import { SimulatorPage } from "@/pages/SimulatorPage";
import { PlayerAnalyticsPage } from "@/pages/PlayerAnalyticsPage";
import { TeamAnalyticsPage } from "@/pages/TeamAnalyticsPage";
import { PredictionsPage } from "@/pages/PredictionsPage";
import { NotFoundPage } from "@/pages/NotFoundPage";
import { ROUTES } from "./constants";

export const router = createBrowserRouter([
  {
    element: <AppLayout />,
    children: [
      { path: ROUTES.HOME, element: <HomePage /> },
      { path: ROUTES.COUNTRY_RANKINGS, element: <RankingsPage /> },
      { path: ROUTES.MATCH_PREDICTOR, element: <PredictorPage /> },
      { path: ROUTES.TOURNAMENT_SIMULATOR, element: <SimulatorPage /> },
      { path: ROUTES.PLAYER_ANALYTICS, element: <PlayerAnalyticsPage /> },
      { path: ROUTES.TEAM_ANALYTICS, element: <TeamAnalyticsPage /> },
      { path: ROUTES.PREDICTIONS, element: <PredictionsPage /> },
      { path: ROUTES.NOT_FOUND, element: <NotFoundPage /> },
    ],
  },
]);
