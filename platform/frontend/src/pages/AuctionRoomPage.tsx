import { useEffect, useRef, useState } from "react";
import { useParams, useSearchParams, useNavigate } from "react-router-dom";
import { API_BASE } from "@/services/api";
import { useAuctionSocket } from "@/hooks/useAuctionSocket";
import { useAuctionStore } from "@/store/auctionStore";
import { useIdentityStore } from "@/store/identityStore";
import { ReconnectionBanner } from "@/components/auction/ReconnectionBanner";
import { AuctionTimer } from "@/components/auction/AuctionTimer";
import { ActivityFeed } from "@/components/auction/ActivityFeed";
import { BidControls } from "@/components/auction/BidControls";
import { PlayerCard } from "@/components/auction/PlayerCard";
import { useAuctionKeyboard } from "@/hooks/useAuctionKeyboard";

type LeagueRules = {
  name?: string;
  squad_size?: number;
  min_gk?: number;
  min_def?: number;
  min_mid?: number;
  min_fwd?: number;
  max_gk?: number;
  max_def?: number;
  max_mid?: number;
  max_fwd?: number;
};

type SquadEntry = {
  id: string;
  position: string;
};

type SquadDetail = {
  id: string;
  name: string;
  position: string;
  flag_code: string;
  club: string;
  purchase_price: number;
};

const POSITION_ORDER = ["GK", "DEF", "MID", "FWD"] as const;
const EMPTY_SQUAD: SquadDetail[] = [];

function getPositionCaps(league: LeagueRules | null) {
  return {
    GK: league?.max_gk ?? 3,
    DEF: league?.max_def ?? 6,
    MID: league?.max_mid ?? 6,
    FWD: league?.max_fwd ?? 5,
  } as Record<(typeof POSITION_ORDER)[number], number>;
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
  const storedUserId = useIdentityStore((state) => state.userId);
  const storedUsername = useIdentityStore((state) => state.username);
  const setStoredUserId = useIdentityStore((state) => state.setUserId);
  const setStoredUsername = useIdentityStore((state) => state.setUsername);
  const paramUserId = searchParams.get("userId") ?? "";
  const paramUsername = searchParams.get("username") ?? "";
  const paramTeamName = searchParams.get("teamName") ?? "";
  const storeStatus = useAuctionStore((s) => s.status);
  const storeTimerSeconds = useAuctionStore((s) => s.timerSeconds);
  const storeCurrentPlayer = useAuctionStore((s) => s.currentPlayer);
  const storeCurrentHighBid = useAuctionStore((s) => s.currentHighBid);
  const storeCurrentBidderId = useAuctionStore((s) => s.currentBidderId);
  const storeMyBudget = useAuctionStore((s) => s.myBudget);
  const storeUserId = useAuctionStore((s) => s.userId);
  const storeMessages = useAuctionStore((s) => s.messages);
  const storeSetLeague = useAuctionStore((s) => s.setLeague);
  const storeReset = useAuctionStore((s) => s.reset);
  const previousLeagueIdRef = useRef<string | null>(null);
  const [localUserId, setLocalUserId] = useState(paramUserId || storedUserId || "");
  const [localUsername, setLocalUsername] = useState(paramUsername || storedUsername || "");
  const storedTeamName = useIdentityStore((state) => state.teamName);
  const localTeamName = paramTeamName || storedTeamName || "";
  const [leagueName, setLeagueName] = useState("");
  const [inviteCode, setInviteCode] = useState("");
  const [leagueRules, setLeagueRules] = useState<LeagueRules | null>(null);
  const [isHost, setIsHost] = useState(false);
  const [showMySquad, setShowMySquad] = useState(false);
  const [cardState, setCardState] = useState<'idle' | 'sold' | 'entering'>('idle');
  const [soldInfo, setSoldInfo] = useState<{ winner: string; isUnsold: boolean } | null>(null);
  const prevPlayerRef = useRef<typeof storeCurrentPlayer>(null);
  const [nominatedName, setNominatedName] = useState<string | null>(null);
  const [centerKey, setCenterKey] = useState(0);

  useEffect(() => {
    // Sync URL params -> persisted identity once on param change or when persisted values become available.
    if (paramUserId) {
      setStoredUserId(paramUserId);
      setLocalUserId(paramUserId);
      return;
    }

    if (!localUserId && storedUserId) {
      setLocalUserId(storedUserId);
    }

    if (paramUsername) {
      setStoredUsername(paramUsername);
      setLocalUsername(paramUsername);
      return;
    }

    if (!localUsername && storedUsername) {
      setLocalUsername(storedUsername);
    }
  }, [paramUserId, paramUsername, storedUserId, storedUsername, setStoredUserId, setStoredUsername]);

  useEffect(() => {
    if (previousLeagueIdRef.current && previousLeagueIdRef.current !== leagueId) {
      storeReset();
    }
    previousLeagueIdRef.current = leagueId || null;
  }, [leagueId]);

  useEffect(() => {
    if (leagueId && localUserId && localUsername) {
      storeSetLeague(leagueId, localUserId, localUsername);
      localStorage.setItem("auction:userId", localUserId);
      localStorage.setItem("auction:username", localUsername);
    }
  }, [leagueId, localUserId, localUsername]);

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
          if (league.invite_code) setInviteCode(league.invite_code);
          setIsHost(league.host_id === localUserId);
        }
      })
      .catch(() => {});
    return () => { mounted = false; };
  }, [leagueId, localUserId]);

  const { placeBid, startAuction, stopAuction, skipPlayer, confirmSale, leaveAuction, pauseAuction, resumeAuction } = useAuctionSocket(leagueId, localUserId, localUsername);
  const maxTimerSeconds = useAuctionStore((s) => s.maxTimerSeconds);
  const upcomingPlayers = useAuctionStore((s) => s.upcomingPlayers);
  const users = useAuctionStore((s) => s.users);
  const positionCaps = getPositionCaps(leagueRules);
  const auctionStatus = storeStatus;
  const connectionStatus = useAuctionStore((s) => s.connectionStatus);
  const currentHighBid = storeCurrentHighBid;
  const isAuctionActive = auctionStatus === "bidding" || auctionStatus === "active";
  const hasBids = currentHighBid > 0;
  const mySquadRaw = useAuctionStore((s) => s.users[localUserId ?? ""]?.squad_details);
  const mySquadPlayers: SquadDetail[] = mySquadRaw ?? EMPTY_SQUAD;

  const joined = Boolean(leagueId && localUserId && localUsername);
  const isCurrentHighBidder = Boolean(storeCurrentBidderId && storeUserId && storeCurrentBidderId === storeUserId && storeCurrentHighBid > 0);

  useAuctionKeyboard({
    onBid: placeBid,
    onConfirmSale: confirmSale,
    currentBid: storeCurrentHighBid,
    myBudget: storeMyBudget,
    isCurrentHighBidder,
    auctionActive: isAuctionActive,
  });

  // Detect player transitions for entrance/sold animations (NO data logic changes)
  useEffect(() => {
    if (!storeCurrentPlayer && prevPlayerRef.current) {
      // Player just cleared — sold
      setCardState('sold');
      setTimeout(() => { setSoldInfo(null); setCardState('idle'); }, 1400);
    }
    if (storeCurrentPlayer && !prevPlayerRef.current) {
      // New player appeared — entrance
      setCardState('entering');
      setTimeout(() => setCardState('idle'), 450);
    }
    prevPlayerRef.current = storeCurrentPlayer;
  }, [storeCurrentPlayer]);

  useEffect(() => {
    if (storeCurrentPlayer?.name) {
      setNominatedName(storeCurrentPlayer.name);
      const timer = setTimeout(() => setNominatedName(null), 500);
      setCenterKey(k => k + 1);
      return () => clearTimeout(timer);
    }
  }, [storeCurrentPlayer?.name]);

  // Parse sold/unsold message from activity feed
  useEffect(() => {
    const lastMsg = storeMessages[0] ?? '';
    if (typeof lastMsg === 'string' && lastMsg.includes('→') && lastMsg.includes('coins')) {
      const isUnsold = lastMsg.includes('No buyer') || lastMsg.includes('went unsold');
      if (isUnsold) {
        setSoldInfo({ winner: '', isUnsold: true });
      } else {
        const match = lastMsg.match(/→\s*(.+?)\s+for/);
        setSoldInfo({ winner: match?.[1]?.trim() ?? 'Winner', isUnsold: false });
      }
    }
  }, [storeMessages]);


  return (
    <>
      <ReconnectionBanner />
      <div className="page-content" style={{ paddingTop: connectionStatus === 'connected' ? undefined : 0 }}>
      <section className="wc-card" style={{ padding: 20, display: "grid", gap: 14 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
          <div>
            <div style={{ color: "var(--color-accent)", fontSize: 11, letterSpacing: "0.16em", textTransform: "uppercase", fontWeight: 700 }}>Auction room</div>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <h1 style={{ margin: "6px 0 0", fontFamily: "var(--font-display)", fontSize: "clamp(2rem, 5vw, 3rem)" }}>{leagueName || (leagueId ? `League ${leagueId.slice(0,8)}...` : 'room')}</h1>
              <button
                onClick={() => navigate('/auction/info')}
                aria-label="Player pool and how to play"
                style={{
                  background: 'rgba(255,255,255,0.06)',
                  border: '1px solid rgba(255,255,255,0.12)',
                  borderRadius: '50%',
                  width: 36,
                  height: 36,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  cursor: 'pointer',
                  color: 'rgba(255,255,255,0.9)',
                  flexShrink: 0,
                }}
                title="Player pool & how to play"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden>
                  <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.2" fill="none" />
                  <rect x="11.5" y="10.5" width="1" height="5" fill="currentColor" />
                  <circle cx="12" cy="7.2" r="0.7" fill="currentColor" />
                </svg>
              </button>
            </div>
          </div>
          <div style={{ display: 'grid', gap: 6, alignItems: 'center', justifyItems: 'end' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span className={`status-dot ${connectionStatus}`} />
              <span style={{ color: connectionStatus === 'connected' ? '#86efac' : connectionStatus === 'reconnecting' ? '#fbbf24' : 'var(--color-text-muted)', fontWeight: 700, fontSize: 13 }}>
                {connectionStatus === 'connected' ? 'Connected' : connectionStatus === 'reconnecting' ? 'Reconnecting...' : 'Disconnected'}
              </span>
            </div>
            {inviteCode && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, background: 'rgba(255,255,255,0.03)', padding: '6px 10px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.06)' }}>
                <div style={{ fontSize: 12, color: 'var(--color-text-muted)', fontWeight: 700 }}>Invite</div>
                <div style={{ fontFamily: 'var(--font-display)', fontWeight: 800, color: '#e3c15c' }}>{inviteCode}</div>
                <button
                  onClick={async () => { try { await navigator.clipboard.writeText(inviteCode); } catch {} }}
                  title="Copy invite code"
                  style={{ background: 'transparent', border: 'none', color: 'rgba(255,255,255,0.8)', cursor: 'pointer' }}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="9" y="9" width="9" height="9" rx="1" stroke="currentColor" strokeWidth="1.2" />
                    <rect x="6" y="6" width="9" height="9" rx="1" stroke="currentColor" strokeWidth="1.2" fill="none" />
                  </svg>
                </button>
              </div>
            )}
          </div>
        </div>

        <div className="layout-3col">
          <label style={{ display: "grid", gap: 6 }}>
            <span style={{ color: "var(--color-text-muted)", fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase" }}>Username</span>
            <input
              value={localUserId}
              onChange={(event) => {
                const value = event.target.value;
                setLocalUserId(value);
                setStoredUserId(value);
                setLocalUsername(value);
                setStoredUsername(value);
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.currentTarget.blur();
                }
              }}
              placeholder="your-username"
              style={inputStyle}
              autoComplete="off"
            />
          </label>
          <label style={{ display: "grid", gap: 6 }}>
            <span style={{ color: "var(--color-text-muted)", fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase" }}>Team name</span>
            <div
              style={{
                ...inputStyle,
                display: "flex",
                alignItems: "center",
                color: "rgba(255,255,255,0.65)",
                userSelect: "none" as const,
              }}
            >
              {localUserId
                ? isHost
                  ? `${localUserId}'s XI`
                  : localTeamName || `${localUserId}'s XI`
                : <span style={{ color: "rgba(255,255,255,0.25)" }}>Enter username first</span>}
            </div>
          </label>
          <div style={{ display: "flex", alignItems: "end", gap: 10, flexWrap: "wrap" }}>
            {isHost && auctionStatus === 'waiting' && (
              <button type="button" onClick={startAuction} disabled={!joined} style={primaryButtonStyle(joined)}>
                START AUCTION
              </button>
            )}
            {isHost && (auctionStatus === 'bidding' || auctionStatus === 'active') && (
              <button
                type="button"
                onClick={pauseAuction}
                style={{
                  ...primaryButtonStyle(true),
                  background: 'rgba(245,158,11,0.15)',
                  border: '1px solid rgba(245,158,11,0.4)',
                  color: '#fbbf24',
                }}
              >
                PAUSE AUCTION
              </button>
            )}
            {isHost && auctionStatus === 'paused' && (
              <button
                type="button"
                onClick={resumeAuction}
                style={{
                  ...primaryButtonStyle(true),
                  background: 'rgba(34,197,94,0.15)',
                  border: '1px solid rgba(34,197,94,0.4)',
                  color: '#4ade80',
                }}
              >
                RESUME AUCTION
              </button>
            )}
            {isHost && (auctionStatus === 'bidding' || auctionStatus === 'active' || auctionStatus === 'processing' || auctionStatus === 'paused') && (
              <button
                type="button"
                onClick={stopAuction}
                style={{
                  ...primaryButtonStyle(true),
                  background: 'rgba(239,68,68,0.15)',
                  border: '1px solid rgba(239,68,68,0.4)',
                  color: '#f87171',
                }}
              >
                STOP AUCTION
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
            {auctionStatus === 'paused' && (
              <div style={{
                fontSize: 13,
                color: '#fbbf24',
                fontFamily: 'var(--font-ui)',
                padding: '10px 16px',
                background: 'rgba(245,158,11,0.08)',
                borderRadius: 8,
                border: '1px solid rgba(245,158,11,0.2)',
              }}>
                ⏸️ Auction paused by the host. Bidding is frozen...
              </div>
            )}
            <button
              type="button"
              onClick={leaveAuction}
              style={{
                padding: '10px 20px',
                borderRadius: 10,
                border: '1px solid rgba(255,255,255,0.12)',
                background: 'rgba(255,255,255,0.04)',
                color: 'rgba(255,255,255,0.6)',
                cursor: 'pointer',
                fontWeight: 600,
                fontSize: 13,
                fontFamily: 'var(--font-ui)',
                transition: 'all 0.2s',
              }}
              onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.08)'; e.currentTarget.style.color = 'rgba(255,255,255,0.9)'; }}
              onMouseLeave={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.04)'; e.currentTarget.style.color = 'rgba(255,255,255,0.6)'; }}
            >
              LEAVE
            </button>
          </div>
        </div>
      </section>

      <div className="auction-room-grid">
        <section className="wc-card" style={{ padding: 18, display: "grid", gap: 12 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div style={{ color: "var(--color-text-muted)", fontSize: 11, fontWeight: 500, letterSpacing: "0.08em", textTransform: "uppercase" }}>Budgets</div>
            <div style={{ color: "var(--color-text-muted)", fontSize: 12 }}>{Object.keys(users).length} managers</div>
          </div>

          <div style={{ display: "grid", gap: 10 }}>
            {Object.entries(users).map(([userIdKey, user]) => {
              const typedUser = user as any;
              const squad = Array.isArray(typedUser.squad) ? (typedUser.squad as SquadEntry[]) : [];
              const counts = getPositionCounts(squad);
              const width = Math.max(8, Math.round(((typedUser.budget_left ?? 0) / Math.max(...Object.values(users).map((entry: any) => entry.budget_left ?? 0), 1)) * 100));
              const isOwnCard = userIdKey === localUserId;

              return (
                <div
                  key={userIdKey}
                  onClick={() => {
                    if (isOwnCard) setShowMySquad(true);
                  }}
                  style={{
                    padding: 12,
                    borderRadius: 16,
                    background: isOwnCard ? "rgba(212,175,55,0.12)" : "rgba(255,255,255,0.04)",
                    border: isOwnCard ? "1px solid rgba(212,175,55,0.3)" : "1px solid rgba(255,255,255,0.06)",
                    cursor: isOwnCard ? "pointer" : "default",
                    transition: "border-color 0.15s",
                  }}
                  onMouseEnter={(event) => {
                    if (isOwnCard) {
                      (event.currentTarget as HTMLDivElement).style.borderColor = "rgba(212,175,55,0.35)";
                    }
                  }}
                  onMouseLeave={(event) => {
                    if (isOwnCard) {
                      (event.currentTarget as HTMLDivElement).style.borderColor = "rgba(255,255,255,0.06)";
                    }
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 10, marginBottom: 8 }}>
                    <div style={{ color: "#fff", fontWeight: 700 }}>{typedUser.username}{isOwnCard ? " (you)" : ""}</div>
                    <div style={{ color: "var(--color-accent)", fontFamily: "var(--font-display)", fontSize: 17, fontWeight: 700, letterSpacing: "0.01em" }}>{typedUser.budget_left} coins</div>
                  </div>
                  {isOwnCard && (
                    <div style={{ color: "rgba(255,255,255,0.52)", fontSize: 11, marginBottom: 8 }}>Click to view squad</div>
                  )}
                  <div style={{ height: 8, borderRadius: 999, background: "rgba(255,255,255,0.08)", overflow: "hidden", marginBottom: 8 }}>
                    <div style={{ width: `${width}%`, height: "100%", background: isOwnCard ? "linear-gradient(90deg, #d4af37, #f7d774)" : "rgba(255,255,255,0.62)" }} />
                  </div>
                  <div style={{ color: "var(--color-text-muted)", fontSize: 12, marginBottom: 8 }}>Squad size: {typedUser.squad_size ?? squad.length}</div>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 8 }}>
                    {POSITION_ORDER.map((pos) => (
                      <div key={pos} style={{ padding: "8px 10px", borderRadius: 12, background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.06)", textAlign: "center" }}>
                        <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: "0.14em", textTransform: "uppercase", color: "rgba(212,175,55,0.75)", lineHeight: 1 }}>{pos}</div>
                        <div style={{ color: "#fff", fontFamily: "var(--font-display)", fontSize: 15, fontWeight: 600, letterSpacing: "0.01em", marginTop: 4 }}>{counts[pos as keyof typeof counts] ?? 0}/{positionCaps[pos]}</div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {storeStatus !== "waiting" ? (
            <AuctionTimer
              seconds={storeTimerSeconds}
              maxSeconds={maxTimerSeconds}
              isActive
              isPaused={storeStatus === "paused"}
            />
          ) : null}
          <div>
            {storeCurrentPlayer ? (
              <div
                key={`${storeCurrentPlayer.id}-${centerKey}`}
                className="wc-card"
                style={{ padding: 0 }}
              >
                <PlayerCard player={storeCurrentPlayer} currentBid={storeCurrentHighBid} isOnBlock />
              </div>
            ) : (cardState === 'sold' && soldInfo) ? (
              soldInfo.isUnsold ? (
                <div
                  className="wc-card"
                  style={{ padding: 32, minHeight: 260, display: 'grid', placeItems: 'center', textAlign: 'center', borderColor: 'rgba(239,68,68,0.3)' }}
                >
                  <div style={{ display: 'grid', gap: 14 }}>
                    <div style={{ fontSize: 52, lineHeight: 1 }}>&#10005;</div>
                    <div style={{ color: '#ef4444', fontFamily: 'var(--font-display)', fontSize: 30, fontWeight: 800, letterSpacing: '-0.02em' }}>UNSOLD</div>
                    <div style={{ color: 'rgba(255,255,255,0.55)', fontSize: 16, fontWeight: 500 }}>No buyer — player returns to the pool</div>
                  </div>
                </div>
              ) : (
                <div
                  className="wc-card player-card-sold"
                  style={{ padding: 32, minHeight: 260, display: 'grid', placeItems: 'center', textAlign: 'center' }}
                >
                  <div style={{ display: 'grid', gap: 14 }}>
                    <div style={{ fontSize: 52, lineHeight: 1 }}>✅</div>
                    <div style={{ color: '#22c55e', fontFamily: 'var(--font-display)', fontSize: 30, fontWeight: 800, letterSpacing: '-0.02em' }}>SOLD</div>
                    <div style={{ color: '#fff', fontSize: 20, fontWeight: 700 }}>{soldInfo.winner}</div>
                  </div>
                </div>
              )
            ) : (
              <div className="wc-card" style={{ padding: 24, minHeight: 260, display: "grid", placeItems: "center", textAlign: "center", color: "var(--color-text-muted)" }}>
                <div style={{ display: "grid", gap: 10 }}>
                  <div style={{ color: "#fff", fontSize: 22, fontWeight: 800 }}>Waiting for the next nomination</div>
                  <div>Once a player is nominated, the live bidding board will appear here.</div>
                </div>
              </div>
            )}
          </div>

          <div>
            <BidControls
              currentBid={storeCurrentHighBid}
              myBudget={storeMyBudget}
              currentBidderId={storeCurrentBidderId}
              myUserId={storeUserId}
              onBid={placeBid}
            />
            {isHost && isAuctionActive && (
              hasBids ? (
                <button
                  type="button"
                  onClick={confirmSale}
                  disabled={!joined}
                  onMouseEnter={(event) => {
                    (event.currentTarget as HTMLButtonElement).style.background = "rgba(34,197,94,0.25)";
                  }}
                  onMouseLeave={(event) => {
                    (event.currentTarget as HTMLButtonElement).style.background = "rgba(34,197,94,0.15)";
                  }}
                  style={{
                    minHeight: 44,
                    width: "100%",
                    marginTop: 10,
                    padding: '0 14px',
                    borderRadius: 14,
                    border: '1px solid rgba(34,197,94,0.35)',
                    background: 'rgba(34,197,94,0.15)',
                    color: '#fff',
                    fontWeight: 700,
                    cursor: joined ? 'pointer' : 'not-allowed',
                  }}
                >
                  Confirm Sale — {currentHighBid.toLocaleString()} coins
                </button>
              ) : (
                <div style={{ marginTop: 10 }}>
                  <button
                    type="button"
                    onClick={() => skipPlayer()}
                    disabled={!joined}
                    style={{
                      minHeight: 44,
                      width: "100%",
                      padding: '0 14px',
                      borderRadius: 14,
                      border: '1px solid rgba(255,255,255,0.12)',
                      background: 'transparent',
                      color: '#fff',
                      fontWeight: 700,
                      cursor: joined ? 'pointer' : 'not-allowed',
                    }}
                  >
                    Skip Player →
                  </button>
                </div>
              )
            )}
            {!isHost && isAuctionActive && hasBids && (
              <div style={{ marginTop: 10, color: "rgba(255,255,255,0.55)", fontSize: 13, textAlign: "center" }}>
                Host can confirm sale at any time
              </div>
            )}
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <ActivityFeed messages={storeMessages} />

          <div className="wc-card" style={{ padding: 18, display: "grid", gap: 12 }}>
            <div style={{ color: "var(--color-text-muted)", fontSize: 11, fontWeight: 500, letterSpacing: "0.08em", textTransform: "uppercase" }}>UP NEXT</div>
            <div style={{ display: "grid", gap: 10 }}>
              {upcomingPlayers.length === 0 ? (
                <div style={{ color: "var(--color-text-muted)", fontSize: 13 }}>Waiting for auction to start...</div>
              ) : (
                upcomingPlayers.map((p, i) => (
                  <div
                    key={`${p.name}-${i}`}
                    style={{ padding: 12, borderRadius: 14, background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.06)", display: "grid", gridTemplateColumns: "auto 1fr auto auto", gap: 10, alignItems: "center" }}
                  >
                    <div style={{ color: "var(--color-text-muted)", fontFamily: "var(--font-display)", fontSize: 15, fontWeight: 600 }}>{i + 1}.</div>
                    <div style={{ color: "#fff", fontWeight: 700 }}>{p.name}</div>
                    <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: "0.14em", textTransform: "uppercase", color: "rgba(212,175,55,0.75)" }}>{p.position}</div>
                    <div style={{ fontFamily: "var(--font-display)", fontSize: 15, fontWeight: 800, color: "#d4af37" }}>{p.tier.toUpperCase().slice(0, 3)}</div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {showMySquad && (
          <>
            <div
              onClick={() => setShowMySquad(false)}
              style={{
                position: "fixed",
                inset: 0,
                background: "rgba(0,0,0,0.55)",
                backdropFilter: "blur(4px)",
                zIndex: 990,
              }}
            />
            <div
              style={{
                position: "fixed",
                left: "50%",
                top: "50%",
                transform: "translate(-50%, -50%)",
                width: "min(720px, calc(100vw - 32px))",
                maxHeight: "min(80vh, 760px)",
                overflow: "auto",
                zIndex: 991,
                borderRadius: 20,
                border: "1px solid rgba(255,255,255,0.12)",
                background: "rgba(12,15,22,0.98)",
                boxShadow: "0 30px 90px rgba(0,0,0,0.45)",
                padding: 20,
                display: "grid",
                gap: 16,
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12 }}>
                <div>
                  <div style={{ color: "var(--color-gold)", fontSize: 11, letterSpacing: "0.16em", textTransform: "uppercase", fontWeight: 700 }}>My Squad</div>
                  <div style={{ color: "#fff", fontSize: 20, fontWeight: 800, marginTop: 4 }}>{localUsername || "My squad"} · {mySquadPlayers.length} players</div>
                </div>
                <button
                  type="button"
                  onClick={() => setShowMySquad(false)}
                  style={{ background: "none", border: "none", color: "rgba(255,255,255,0.4)", fontSize: 20, cursor: "pointer", padding: 4 }}
                  aria-label="Close squad panel"
                >
                  ✕
                </button>
              </div>

              <div style={{ display: "grid", gap: 14 }}>
                {POSITION_ORDER.map((position) => {
                  const positionPlayers = mySquadPlayers.filter((player) => player.position === position);
                  if (positionPlayers.length === 0) return null;

                  return (
                    <div key={position} style={{ display: "grid", gap: 8 }}>
                      <div style={{ color: "var(--color-text-muted)", fontSize: 12, letterSpacing: "0.12em", textTransform: "uppercase", fontWeight: 700 }}>{position} · {positionPlayers.length}</div>
                      <div style={{ display: "grid", gap: 8 }}>
                        {positionPlayers.map((player) => (
                          <div key={player.id} style={{ display: "grid", gridTemplateColumns: "auto 1fr auto", gap: 12, alignItems: "center", padding: 12, borderRadius: 14, background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.06)" }}>
                            <img
                              src={`https://flagcdn.com/w40/${player.flag_code || 'un'}.png`}
                              alt=""
                              style={{ width: 24, height: 18, borderRadius: 2, objectFit: "cover" }}
                            />
                            <div style={{ display: "grid", gap: 2 }}>
                              <div style={{ color: "#fff", fontWeight: 700 }}>{player.name}</div>
                              <div style={{ color: "var(--color-text-muted)", fontSize: 12 }}>{player.club}</div>
                            </div>
                            <div style={{ color: "var(--color-gold)", fontWeight: 800 }}>{(player.purchase_price ?? 0).toLocaleString()} coins</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}

                {mySquadPlayers.length === 0 && (
                  <div style={{ color: "var(--color-text-muted)", textAlign: "center", padding: "24px 0" }}>No players yet — win some bids!</div>
                )}
              </div>
            </div>
          </>
        )}
      </div>
      </div>
    </>
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