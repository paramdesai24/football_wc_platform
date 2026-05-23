import { createBrowserRouter } from "react-router-dom";
import { AppLayout } from "@/layouts/AppLayout";
import { ROUTES } from "./constants";

// Lazy loading for code splitting
import { lazy, Suspense } from "react";

const DashboardPage = lazy(() => import("@/pages/DashboardPage"));
const PredictionsPage = lazy(() => import("@/pages/PredictionsPage"));
const RankingsPage = lazy(() => import("@/pages/RankingsPage"));
const TeamAnalyticsPage = lazy(() => import("@/pages/TeamAnalyticsPage"));
const TournamentPage = lazy(() => import("@/pages/TournamentPage"));
const PlayAsTeamPage = lazy(() => import("@/pages/PlayAsTeamPage"));
const NotFoundPage = lazy(() => import("@/pages/NotFoundPage"));

function Loader() {
  return (
    <div className="page-container" style={{ textAlign: "center", padding: "60px 0" }}>
      <span className="spinner" />
    </div>
  );
}

function SuspenseWrap({ children }: { children: React.ReactNode }) {
  return <Suspense fallback={<Loader />}>{children}</Suspense>;
}

export const router = createBrowserRouter([
  {
    element: <AppLayout />,
    children: [
      { path: ROUTES.HOME, element: <SuspenseWrap><DashboardPage /></SuspenseWrap> },
      { path: ROUTES.PREDICTIONS, element: <SuspenseWrap><PredictionsPage /></SuspenseWrap> },
      { path: ROUTES.RANKINGS, element: <SuspenseWrap><RankingsPage /></SuspenseWrap> },
      { path: ROUTES.TEAM_ANALYTICS, element: <SuspenseWrap><TeamAnalyticsPage /></SuspenseWrap> },
      { path: ROUTES.TOURNAMENT_SIMULATOR, element: <SuspenseWrap><TournamentPage /></SuspenseWrap> },
      { path: ROUTES.PLAY_AS_TEAM, element: <SuspenseWrap><PlayAsTeamPage /></SuspenseWrap> },
      { path: ROUTES.NOT_FOUND, element: <SuspenseWrap><NotFoundPage /></SuspenseWrap> },
    ],
  },
]);
