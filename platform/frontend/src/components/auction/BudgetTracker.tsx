import type { RoomUser } from "@/store/auctionStore";

interface BudgetTrackerProps {
  users: Record<string, RoomUser>;
  myUserId: string | null;
}

export function BudgetTracker({ users, myUserId }: BudgetTrackerProps) {
  const entries = Object.entries(users);
  const topBudget = Math.max(...entries.map(([, user]) => user.budget_left), 1);

  return (
    <div className="wc-card" style={{ padding: 18, display: "grid", gap: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div style={{ color: "var(--color-text-secondary)", fontSize: 11, letterSpacing: "0.14em", textTransform: "uppercase" }}>Budgets</div>
        <div style={{ color: "var(--color-text-muted)", fontSize: 12 }}>{entries.length} managers</div>
      </div>

      <div style={{ display: "grid", gap: 10 }}>
        {entries.map(([userId, user]) => {
          const width = Math.max(8, Math.round((user.budget_left / topBudget) * 100));
          return (
            <div key={userId} style={{ padding: 12, borderRadius: 16, background: userId === myUserId ? "rgba(212,175,55,0.12)" : "rgba(255,255,255,0.04)", border: userId === myUserId ? "1px solid rgba(212,175,55,0.3)" : "1px solid rgba(255,255,255,0.06)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 10, marginBottom: 8 }}>
                <div style={{ color: "#fff", fontWeight: 700 }}>{user.username}{userId === myUserId ? " (you)" : ""}</div>
                <div style={{ color: "var(--color-gold)", fontFamily: "var(--font-display)", fontWeight: 800 }}>{user.budget_left} coins</div>
              </div>
              <div style={{ height: 8, borderRadius: 999, background: "rgba(255,255,255,0.08)", overflow: "hidden", marginBottom: 8 }}>
                <div style={{ width: `${width}%`, height: "100%", background: userId === myUserId ? "linear-gradient(90deg, #d4af37, #f7d774)" : "rgba(255,255,255,0.62)" }} />
              </div>
              <div style={{ color: "var(--color-text-muted)", fontSize: 12 }}>Squad size: {user.squad_size}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}