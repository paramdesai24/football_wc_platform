import { Navigate, Outlet, useLocation } from "react-router-dom";
import { ROUTES } from "@/routes/constants";

interface ProtectedRouteProps {
  isAllowed: boolean;
  redirectTo?: string;
}

export function ProtectedRoute({ isAllowed, redirectTo = ROUTES.HOME }: ProtectedRouteProps) {
  const location = useLocation();

  if (!isAllowed) {
    return <Navigate to={redirectTo} replace state={{ from: location.pathname }} />;
  }

  return <Outlet />;
}
