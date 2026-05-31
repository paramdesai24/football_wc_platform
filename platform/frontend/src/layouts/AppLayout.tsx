import { Outlet } from "react-router-dom";
import { TopNavBar } from "@/components/layout/TopNavBar";
import { ToastContainer } from "@/components/ui/ToastContainer";
import { PageWrapper } from "@/components/layout/PageWrapper";

export function AppLayout() {
  return (
    <div className="wc-app-shell">
      <div className="wc-background" aria-hidden="true" />
      <div className="wc-shell-content" style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
        <TopNavBar />
        <main style={{ flex: 1, paddingBottom: 28 }}>
          <PageWrapper>
            <Outlet />
          </PageWrapper>
        </main>
        <ToastContainer />
        <footer className="wc-footer" style={{ padding: "12px 20px", textAlign: "center", fontSize: "0.75rem" }}>
          FC Analytics · live football intelligence · broadcast-ready runtime
        </footer>
      </div>
    </div>
  );
}
