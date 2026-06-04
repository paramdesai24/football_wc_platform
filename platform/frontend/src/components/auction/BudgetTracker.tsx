import type { RoomUser } from "@/store/auctionStore";
import { useAuctionStore } from "@/store/auctionStore";
import { useEffect, useRef, useState } from "react";
import { SpringNumber } from "@/components/ui/SpringNumber";

interface BudgetTrackerProps {
  users: Record<string, RoomUser>;
  myUserId: string | null;
}

function AnimatedBudget({ value, className }: { value: number; className?: string }) {
  return <SpringNumber value={value} className={className} formatter={n => Math.round(n).toLocaleString() + " coins"} />;
}

export function BudgetTracker({ users, myUserId }: BudgetTrackerProps) {
  const entries = Object.entries(users);
  const topBudget = Math.max(...entries.map(([, user]) => user.budget_left), 1);
  const currentBidderId = useAuctionStore(s => s.currentBidderId);
  const [outbid, setOutbid] = useState(false);
  const prevBidderRef = useRef<string | null>(null);

  useEffect(() => {
    if (
      currentBidderId &&
      currentBidderId !== myUserId &&
      prevBidderRef.current === myUserId
    ) {
      setOutbid(true);
      setTimeout(() => setOutbid(false), 500);
    }
    prevBidderRef.current = currentBidderId;
  }, [currentBidderId, myUserId]);

  return (
    <div className="wc-card" style={{ padding: 18, display: "grid", gap: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div style={{ fontSize: 11, fontWeight: 500, letterSpacing: "0.08em", textTransform: "uppercase", color: "rgba(255,255,255,0.38)", lineHeight: 1 }}>Budgets</div>
        <div style={{ color: "var(--color-text-muted)", fontSize: 12 }}>{entries.length} managers</div>
      </div>

      <div style={{ display: "grid", gap: 10 }}>
        {entries.map(([userId, user]) => {
          const width = Math.max(8, Math.round((user.budget_left / topBudget) * 100));
          return (
            <div key={userId} style={{ padding: 12, borderRadius: 16, background: userId === myUserId ? "rgba(212,175,55,0.12)" : "rgba(255,255,255,0.04)", border: userId === myUserId ? "1px solid rgba(212,175,55,0.3)" : "1px solid rgba(255,255,255,0.06)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 10, marginBottom: 8 }}>
                <div style={{ color: "#fff", fontWeight: 700 }}>{user.username}{userId === myUserId ? " (you)" : ""}</div>
                <div
                  className={userId === myUserId && outbid ? "outbid-flash" : ""}
                  style={{
                    color: "#d4af37",
                    lineHeight: 1.1,
                    fontFamily: "var(--font-display)",
                    fontSize: "clamp(16px,2vw,22px)",
                    fontWeight: 700,
                    letterSpacing: "0.01em"
                  }}
                >
                  <AnimatedBudget value={user.budget_left} />
                </div>
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