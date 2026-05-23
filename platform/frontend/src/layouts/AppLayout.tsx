import { Outlet } from "react-router-dom";
import { TopNavBar } from "@/components/layout/TopNavBar";

export function AppLayout() {
  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <TopNavBar />
      <main style={{ flex: 1, paddingBottom: 24 }}>
        <Outlet />
      </main>
      <footer
        style={{
          borderTop: "1px solid var(--color-border)",
          padding: "12px 20px",
          textAlign: "center",
          fontSize: "0.75rem",
          color: "var(--color-text-muted)",
        }}
      >
        WC26 Intelligence Platform · Live backend intelligence · Stable runtime
      </footer>
    </div>
  );
}
