import { Outlet, useLocation } from "react-router-dom";
import { TopNavBar } from "@/components/layout/TopNavBar";
import { ToastContainer } from "@/components/ui/ToastContainer";
import { PageWrapper } from "@/components/layout/PageWrapper";

export function AppLayout() {
  const { pathname } = useLocation();
  const isAuctionRoom = pathname.startsWith('/auction/room');

  return (
    <div className="wc-app-shell">
      <div className="wc-background" aria-hidden="true" />
      <div className="wc-shell-content" style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
        <TopNavBar />
        <main style={{ flex: 1, paddingBottom: isAuctionRoom ? 0 : 28 }}>
          <PageWrapper>
            <Outlet />
          </PageWrapper>
        </main>
        <ToastContainer />
        {!isAuctionRoom && (
          <footer className="wc-footer" style={{ padding: "12px 20px", textAlign: "center", fontSize: "0.75rem" }}>
            FC Analytics · live football intelligence · broadcast-ready runtime
          </footer>
        )}
      </div>
    </div>
  );
}
