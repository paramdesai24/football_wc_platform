import { useEffect, useRef, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { useAuctionSocket } from "@/hooks/useAuctionSocket";
import { useAuctionStore } from "@/store/auctionStore";
import { AuctionTimer } from "@/components/auction/AuctionTimer";
import { ActivityFeed } from "@/components/auction/ActivityFeed";
import { BidControls } from "@/components/auction/BidControls";
import { BudgetTracker } from "@/components/auction/BudgetTracker";
import { PlayerCard } from "@/components/auction/PlayerCard";

export default function AuctionRoomPage() {
  const { id: leagueId = "" } = useParams();
  const [searchParams] = useSearchParams();
  const paramUserId = searchParams.get("userId") ?? "";
  const paramUsername = searchParams.get("username") ?? paramUserId;
  const store = useAuctionStore();
  const previousLeagueIdRef = useRef<string | null>(null);
  const [userId, setUserId] = useState(paramUserId);
  const [username, setUsername] = useState(paramUsername);

  useEffect(() => {
    setUserId(paramUserId);
    setUsername(paramUsername);
  }, [paramUserId, paramUsername]);

  useEffect(() => {
    if (previousLeagueIdRef.current && previousLeagueIdRef.current !== leagueId) {
      store.reset();
    }
    previousLeagueIdRef.current = leagueId || null;
  }, [leagueId]);

  useEffect(() => {
    if (leagueId && userId && username) {
      store.setLeague(leagueId, userId, username);
      localStorage.setItem("auction:userId", userId);
      localStorage.setItem("auction:username", username);
    }
  }, [leagueId, userId, username]);

  const { placeBid, startAuction, isConnected } = useAuctionSocket(leagueId, userId, username);
  const maxTimerSeconds = useAuctionStore((s) => s.maxTimerSeconds);
  const upcomingPlayers = useAuctionStore((s) => s.upcomingPlayers);

  const joined = Boolean(leagueId && userId && username);

  return (
    <div className="page-container" style={{ display: "grid", gap: 16 }}>
      <section className="wc-card" style={{ padding: 20, display: "grid", gap: 14 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
          <div>
            <div style={{ color: "var(--color-accent)", fontSize: 11, letterSpacing: "0.16em", textTransform: "uppercase", fontWeight: 700 }}>Auction room</div>
            <h1 style={{ margin: "6px 0 0", fontFamily: "var(--font-display)", fontSize: "clamp(2rem, 5vw, 3rem)" }}>League {leagueId || "room"}</h1>
          </div>
          <div style={{ color: isConnected ? "#86efac" : "var(--color-text-muted)", fontWeight: 700 }}>{isConnected ? "Connected" : "Disconnected"}</div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: 12 }}>
          <label style={{ display: "grid", gap: 6 }}>
            <span style={{ color: "var(--color-text-muted)", fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase" }}>User ID</span>
            <input value={userId} onChange={(event) => setUserId(event.target.value)} placeholder="manager-1" style={inputStyle} />
          </label>
          <label style={{ display: "grid", gap: 6 }}>
            <span style={{ color: "var(--color-text-muted)", fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase" }}>Username</span>
            <input value={username} onChange={(event) => setUsername(event.target.value)} placeholder="Your name" style={inputStyle} />
          </label>
          <div style={{ display: "flex", alignItems: "end", gap: 10 }}>
            <button type="button" onClick={startAuction} disabled={!joined} style={primaryButtonStyle(joined)}>
              START AUCTION
            </button>
          </div>
        </div>
      </section>

      <div className="auction-room-grid">
        <BudgetTracker users={store.users} myUserId={store.userId} />

        <div style={{ display: "grid", gap: 16 }}>
          {store.status !== "waiting" ? <AuctionTimer seconds={store.timerSeconds} maxSeconds={maxTimerSeconds} isActive /> : null}
          {store.currentPlayer ? (
            <PlayerCard player={store.currentPlayer} currentBid={store.currentHighBid} isOnBlock />
          ) : (
            <div className="wc-card" style={{ padding: 24, minHeight: 260, display: "grid", placeItems: "center", textAlign: "center", color: "var(--color-text-muted)" }}>
              <div style={{ display: "grid", gap: 10 }}>
                <div style={{ color: "#fff", fontSize: 22, fontWeight: 800 }}>Waiting for the next nomination</div>
                <div>Once a player is nominated, the live bidding board will appear here.</div>
              </div>
            </div>
          )}

          <BidControls
            currentBid={store.currentHighBid}
            myBudget={store.myBudget}
            currentBidderId={store.currentBidderId}
            myUserId={store.userId}
            onBid={placeBid}
          />
        </div>

        <div style={{ display: "grid", gap: 16 }}>
          <ActivityFeed messages={store.messages} />

          <div className="wc-card" style={{ padding: 18, display: "grid", gap: 12 }}>
            <div style={{ color: "var(--color-text-secondary)", fontSize: 11, letterSpacing: "0.14em", textTransform: "uppercase" }}>UP NEXT</div>
            <div style={{ display: "grid", gap: 10 }}>
              {upcomingPlayers.length === 0 ? (
                <div style={{ color: "var(--color-text-muted)", fontSize: 13 }}>Waiting for auction to start...</div>
              ) : (
                upcomingPlayers.map((p, i) => (
                  <div key={`${p.name}-${i}`} style={{ padding: 12, borderRadius: 14, background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.06)", display: "grid", gridTemplateColumns: "auto 1fr auto auto", gap: 10, alignItems: "center" }}>
                    <div style={{ color: "var(--color-text-muted)", fontSize: 12, fontWeight: 700 }}>{i + 1}.</div>
                    <div style={{ color: "#fff", fontWeight: 700 }}>{p.name}</div>
                    <div style={{ color: "var(--color-text-muted)", fontSize: 12 }}>{p.position}</div>
                    <div style={{ color: "var(--color-gold)", fontWeight: 800, fontSize: 12 }}>{p.tier.toUpperCase().slice(0, 3)}</div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

const inputStyle: React.CSSProperties = {
  height: 44,
  borderRadius: 14,
  border: "1px solid rgba(255,255,255,0.12)",
  background: "rgba(255,255,255,0.04)",
  color: "#fff",
  padding: "0 14px",
  fontSize: 15,
  outline: "none",
};

function primaryButtonStyle(enabled: boolean): React.CSSProperties {
  return {
    minHeight: 44,
    padding: "0 18px",
    borderRadius: 14,
    border: "none",
    background: enabled ? "linear-gradient(135deg, #d4af37, #f7d774)" : "rgba(255,255,255,0.12)",
    color: enabled ? "#08101f" : "rgba(255,255,255,0.55)",
    fontWeight: 800,
    letterSpacing: "0.08em",
    cursor: enabled ? "pointer" : "not-allowed",
  };
}