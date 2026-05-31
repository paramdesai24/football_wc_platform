import { useEffect, useRef, useState } from "react";
import { useParams, useSearchParams, useNavigate } from "react-router-dom";
import { apiGet, API_BASE } from "@/services/api";
import { useAuctionSocket } from "@/hooks/useAuctionSocket";
import { useAuctionStore } from "@/store/auctionStore";
import { AuctionTimer } from "@/components/auction/AuctionTimer";
import { ActivityFeed } from "@/components/auction/ActivityFeed";
import { BidControls } from "@/components/auction/BidControls";
import { PlayerCard } from "@/components/auction/PlayerCard";

type LeagueRules = {
  name?: string;
  squad_size?: number;
  min_gk?: number;
  min_def?: number;
  min_mid?: number;
  min_fwd?: number;
};

type SquadEntry = {
  id: string;
  position: string;
};

const POSITION_ORDER = ["GK", "DEF", "MID", "FWD"] as const;

function getPositionCaps(league: LeagueRules | null) {
  const squadSize = league?.squad_size ?? 15;
  const minByPos = {
    GK: league?.min_gk ?? 2,
    DEF: league?.min_def ?? 5,
    MID: league?.min_mid ?? 5,
    FWD: league?.min_fwd ?? 3,
  };
  const totalMin = minByPos.GK + minByPos.DEF + minByPos.MID + minByPos.FWD;

  return POSITION_ORDER.reduce((acc, pos) => {
    const otherMins = totalMin - minByPos[pos];
    acc[pos] = Math.max(0, squadSize - otherMins);
    return acc;
  }, {} as Record<(typeof POSITION_ORDER)[number], number>);
}

function getPositionCounts(squad: SquadEntry[] | undefined) {
  return (squad ?? []).reduce(
    (acc, player) => {
      const position = player.position as keyof typeof acc;
      if (position in acc) {
        acc[position] += 1;
      }
      return acc;
    },
    { GK: 0, DEF: 0, MID: 0, FWD: 0 },
  );
}

export default function AuctionRoomPage() {
  const navigate = useNavigate();
  const { id: leagueId = "" } = useParams();
  const [searchParams] = useSearchParams();
  const paramUserId = searchParams.get("userId") ?? "";
  const paramUsername = searchParams.get("username") ?? paramUserId;
  const store = useAuctionStore();
  const previousLeagueIdRef = useRef<string | null>(null);
  const [userId, setUserId] = useState(paramUserId);
  const [username, setUsername] = useState(paramUsername);
  const [leagueName, setLeagueName] = useState("");
  const [leagueRules, setLeagueRules] = useState<LeagueRules | null>(null);
  const [isHost, setIsHost] = useState(false);

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

  useEffect(() => {
    if (!leagueId) return;
    let mounted = true;
    fetch(`${API_BASE}/api/v1/leagues/${leagueId}`)
      .then(r => r.json())
      .then((data) => {
        if (!mounted) return;
        const league = data.league;
        if (league) {
          setLeagueRules(league);
          if (league.name) setLeagueName(league.name);
          setIsHost(league.host_id === userId);
        }
      })
      .catch(() => {});
    return () => { mounted = false; };
  }, [leagueId, userId]);

  const { placeBid, startAuction, isConnected } = useAuctionSocket(leagueId, userId, username);
  const maxTimerSeconds = useAuctionStore((s) => s.maxTimerSeconds);
  const upcomingPlayers = useAuctionStore((s) => s.upcomingPlayers);
  const users = useAuctionStore((s) => s.users);
  const positionCaps = getPositionCaps(leagueRules);
  const auctionStatus = useAuctionStore((s) => s.status);

  const joined = Boolean(leagueId && userId && username);

  return (
    <div className="page-content">
      <section className="wc-card" style={{ padding: 20, display: "grid", gap: 14 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
          <div>
            <div style={{ color: "var(--color-accent)", fontSize: 11, letterSpacing: "0.16em", textTransform: "uppercase", fontWeight: 700 }}>Auction room</div>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <h1 style={{ margin: "6px 0 0", fontFamily: "var(--font-display)", fontSize: "clamp(2rem, 5vw, 3rem)" }}>{leagueName || (leagueId ? `League ${leagueId.slice(0,8)}...` : 'room')}</h1>
              <button
                onClick={() => navigate('/auction/info')}
                style={{
                  background: 'rgba(255,255,255,0.06)',
                  border: '1px solid rgba(255,255,255,0.12)',
                  borderRadius: '50%',
                  width: 34, height: 34,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  cursor: 'pointer',
                  fontSize: 16,
                  color: 'rgba(255,255,255,0.6)',
                  flexShrink: 0,
                }}
                title="Player pool & how to play"
              >
                ℹ️
              </button>
            </div>
          </div>
          <div style={{ color: isConnected ? "#86efac" : "var(--color-text-muted)", fontWeight: 700 }}>{isConnected ? "Connected" : "Disconnected"}</div>
        </div>

        <div className="layout-3col">
          <label style={{ display: "grid", gap: 6 }}>
            <span style={{ color: "var(--color-text-muted)", fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase" }}>User ID</span>
            <input value={userId} onChange={(event) => setUserId(event.target.value)} placeholder="manager-1" style={inputStyle} />
          </label>
          <label style={{ display: "grid", gap: 6 }}>
            <span style={{ color: "var(--color-text-muted)", fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase" }}>Username</span>
            <input value={username} onChange={(event) => setUsername(event.target.value)} placeholder="Your name" style={inputStyle} />
          </label>
          <div style={{ display: "flex", alignItems: "end", gap: 10 }}>
            {isHost && (
              <button type="button" onClick={startAuction} disabled={!joined} style={primaryButtonStyle(joined)}>
                START AUCTION
              </button>
            )}
            {!isHost && auctionStatus === 'waiting' && (
              <div style={{
                fontSize: 13,
                color: 'rgba(255,255,255,0.45)',
                fontFamily: 'var(--font-ui)',
                padding: '10px 16px',
                background: 'rgba(255,255,255,0.04)',
                borderRadius: 8,
                border: '1px solid rgba(255,255,255,0.08)',
              }}>
                ⏳ Waiting for the host to start the auction...
              </div>
            )}
          </div>
        </div>
      </section>

      <div className="auction-room-grid">
        <section className="wc-card" style={{ padding: 18, display: "grid", gap: 12 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div style={{ color: "var(--color-text-secondary)", fontSize: 11, letterSpacing: "0.14em", textTransform: "uppercase" }}>Budgets</div>
            <div style={{ color: "var(--color-text-muted)", fontSize: 12 }}>{Object.keys(users).length} managers</div>
          </div>

          <div style={{ display: "grid", gap: 10 }}>
            {Object.entries(users).map(([userIdKey, user]) => {
              const typedUser = user as any;
              const squad = Array.isArray(typedUser.squad) ? (typedUser.squad as SquadEntry[]) : [];
              const counts = getPositionCounts(squad);
              const width = Math.max(8, Math.round(((typedUser.budget_left ?? 0) / Math.max(...Object.values(users).map((entry: any) => entry.budget_left ?? 0), 1)) * 100));

              return (
                <div key={userIdKey} style={{ padding: 12, borderRadius: 16, background: userIdKey === store.userId ? "rgba(212,175,55,0.12)" : "rgba(255,255,255,0.04)", border: userIdKey === store.userId ? "1px solid rgba(212,175,55,0.3)" : "1px solid rgba(255,255,255,0.06)" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 10, marginBottom: 8 }}>
                    <div style={{ color: "#fff", fontWeight: 700 }}>{typedUser.username}{userIdKey === store.userId ? " (you)" : ""}</div>
                    <div style={{ color: "var(--color-gold)", fontFamily: "var(--font-display)", fontWeight: 800 }}>{typedUser.budget_left} coins</div>
                  </div>
                  <div style={{ height: 8, borderRadius: 999, background: "rgba(255,255,255,0.08)", overflow: "hidden", marginBottom: 8 }}>
                    <div style={{ width: `${width}%`, height: "100%", background: userIdKey === store.userId ? "linear-gradient(90deg, #d4af37, #f7d774)" : "rgba(255,255,255,0.62)" }} />
                  </div>
                  <div style={{ color: "var(--color-text-muted)", fontSize: 12, marginBottom: 8 }}>Squad size: {typedUser.squad_size ?? squad.length}</div>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 8 }}>
                    {POSITION_ORDER.map((pos) => (
                      <div key={pos} style={{ padding: "8px 10px", borderRadius: 12, background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.06)", textAlign: "center" }}>
                        <div style={{ color: "var(--color-text-muted)", fontSize: 10, letterSpacing: "0.08em", textTransform: "uppercase" }}>{pos}</div>
                        <div style={{ color: "#fff", fontWeight: 800, marginTop: 4 }}>{counts[pos as keyof typeof counts] ?? 0}/{positionCaps[pos]}</div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </section>

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