import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { API_BASE } from "@/services/api";
import { EmptyState } from "@/components/ui/EmptyState";
import { SpringNumber } from "@/components/ui/SpringNumber";

type LeaderboardRow = {
  rank: number;
  rank_change?: number | null;
  user_id?: string;
  team_name?: string;
  total_points?: number;
  budget_left?: number;
  squad_size?: number;
};

type LeagueData = {
  name?: string;
  squad_size?: number;
  status?: string;
};

function rowBorder(rank: number): React.CSSProperties {
  if (rank === 1) return { borderLeft: "3px solid var(--wc-gold)" };
  if (rank === 2) return { borderLeft: "3px solid rgba(192,192,192,0.6)" };
  if (rank === 3) return { borderLeft: "3px solid rgba(205,127,50,0.6)" };
  return {};
}

export default function LeagueLeaderboardPage() {
  const { id = "" } = useParams();
  const [leaderboard, setLeaderboard] = useState<LeaderboardRow[]>([]);
  const [league, setLeague] = useState<LeagueData | null>(null);
  const [updatedAt, setUpdatedAt] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const CACHE_KEY    = `leaderboard_cache_${id}`;
  const CACHE_TTL_MS = 3 * 24 * 60 * 60 * 1000; // 3 days

  async function fetchLeaderboard() {
    try {
      // ── Check localStorage cache ──
      try {
        const cached = localStorage.getItem(CACHE_KEY);
        if (cached) {
          const { data, timestamp } = JSON.parse(cached);
          const age = Date.now() - timestamp;
          if (age < CACHE_TTL_MS) {
            setLeague(data.leagueData?.league ?? null);
            setLeaderboard(Array.isArray(data.leaderboard) ? data.leaderboard : []);
            setUpdatedAt(new Date(timestamp).toLocaleString());
            setLoading(false);
            return;
          }
        }
      } catch { /* ignore corrupt cache */ }

      // ── Fetch fresh data ──
      const [leagueRes, leaderboardRes] = await Promise.all([
        fetch(`${API_BASE}/api/v1/leagues/${id}`),
        fetch(`${API_BASE}/api/v1/leagues/${id}/leaderboard`),
      ]);
      const leagueData = await leagueRes.json();
      const leaderboardData = await leaderboardRes.json();
      if (!leagueRes.ok) throw new Error(leagueData.detail ?? "Failed to load league");
      if (!leaderboardRes.ok) throw new Error(leaderboardData.detail ?? "Failed to load leaderboard");

      const freshLeaderboard = Array.isArray(leaderboardData.leaderboard) ? leaderboardData.leaderboard : [];
      setLeague(leagueData.league ?? null);
      setLeaderboard(freshLeaderboard);
      const now = Date.now();
      setUpdatedAt(new Date(now).toLocaleString());
      setError("");

      // ── Save to cache ──
      try {
        localStorage.setItem(CACHE_KEY, JSON.stringify({
          data: { leagueData, leaderboard: freshLeaderboard },
          timestamp: now,
        }));
      } catch { /* storage full — skip caching */ }
    } catch (error: unknown) {
      setError(error instanceof Error ? error.message : String(error));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchLeaderboard();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  return (
    <div className="page-container" style={{ display: "grid", gap: 18 }}>
      <section className="wc-card section-card" style={{ padding: 24, display: "grid", gap: 10 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span className="status-dot connected" />
          <div className="eyebrow">Live leaderboard</div>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 16, alignItems: "flex-end", flexWrap: "wrap" }}>
          <div style={{ display: "grid", gap: 4 }}>
            <h1 className="page-title" style={{ fontSize: "clamp(2rem, 4vw, 3rem)", marginBottom: 0 }}>{league?.name || `League ${id}`}</h1>
            <p className="page-sub" style={{ maxWidth: 760, margin: 0 }}>Live league standings, updated automatically every 72 hours.</p>
          </div>
          <div style={{ fontFamily: "var(--font-display)", fontSize: 18, fontWeight: 700, color: "#fff" }}>{league?.squad_size ?? 0} squad</div>
        </div>
      </section>

      {error && <div style={{ color: "#f87171", fontSize: 13 }}>{error}</div>}

      {/* Best XI scoring note */}
      <section style={{
        background: "rgba(167,139,250,0.05)",
        border: "1px solid rgba(167,139,250,0.2)",
        borderRadius: 14,
        padding: "12px 18px",
        display: "flex",
        alignItems: "center",
        gap: 12,
        fontSize: 12,
        color: "rgba(255,255,255,0.7)",
        fontFamily: "var(--font-ui)",
      }}>
        <span>⚽</span>
        <span>
          <strong style={{ color: "#a78bfa" }}>Best XI rule:</strong>{" "}
          Team points are calculated from the top <strong>1 GK · 4 DEF · 3 MID · 3 FWD</strong> by points each update cycle. The best performers automatically replace lower-scoring squad members.
        </span>
      </section>

      {league?.status === "forfeited" && (
        <section style={forfeitedBannerStyle}>
          <span style={{ fontSize: 24, filter: 'drop-shadow(0 0 4px rgba(239,68,68,0.3))' }}>⚠️</span>
          <div>
            <h3 style={{ margin: "0 0 4px 0", fontSize: 15, fontWeight: 700, color: "#f87171", fontFamily: "var(--font-display)" }}>League Forfeited</h3>
            <p style={{ margin: 0, fontSize: 13, opacity: 0.8, lineHeight: 1.5 }}>
              This league has been forfeited because no participant met the minimum roster position and size requirements.
            </p>
          </div>
        </section>
      )}

      <section className="wc-card" style={{ padding: 0, overflow: "hidden" }}>
        <div style={{ padding: 18, borderBottom: "1px solid rgba(255,255,255,0.08)" }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div className="eyebrow">League standings</div>
              <h2 className="wc-section-title" style={{ margin: 0 }}>Current standings</h2>
            </div>
          </div>
        </div>

        {loading ? (
          <div style={{ padding: 24 }}>Loading leaderboard...</div>
        ) : leaderboard.every((member) => Number(member.total_points ?? 0) === 0) ? (
          <div style={{ padding: 18 }}>
            <EmptyState
              icon="🏁"
              title="No points yet"
              description="No matches have been scored for this league yet. Once results are processed, the leaderboard will populate automatically."
            />
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "separate", borderSpacing: 0 }}>
              <thead>
                <tr style={{ textAlign: "left", color: "rgba(255,255,255,0.72)", fontSize: 11, letterSpacing: "0.14em", textTransform: "uppercase" }}>
                  <Th>Rank</Th>
                  <Th>Team</Th>
                  <Th>User</Th>
                  <Th>Points</Th>
                  <Th>Squad Size</Th>
                  <Th>Budget Left</Th>
                </tr>
              </thead>
              <tbody>
                {leaderboard.map((row) => (
                  <LeaderboardRow key={`${row.rank}-${row.user_id}`} row={row} />
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div style={{ padding: "12px 18px 18px", display: "flex", justifyContent: "space-between", alignItems: "center", color: "var(--color-text-secondary)", fontSize: 12, flexWrap: "wrap", gap: 8 }}>
          <span>Last updated: {updatedAt || "--"}</span>
          <span style={{ color: "rgba(255,255,255,0.5)" }}>🕒 Standings and player points are automatically updated every 72 hours</span>
        </div>
      </section>
    </div>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return <th style={{ padding: "14px 18px", borderBottom: "1px solid rgba(255,255,255,0.08)" }}>{children}</th>;
}

function Td({ children }: { children: React.ReactNode }) {
  return <td style={{ padding: "16px 18px", borderBottom: "1px solid rgba(255,255,255,0.06)", color: "#fff", verticalAlign: "middle" }}>{children}</td>;
}

function LeaderboardRow({ row, className }: { row: LeaderboardRow; className?: string }) {
  return (
    <tr
      className={className}
      style={{
        ...rowBorder(row.rank),
        background: row.rank <= 3 ? "rgba(255,255,255,0.02)" : "transparent",
      }}
    >
      <Td>
        <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
          <span>{row.rank}</span>
          {row.rank_change != null && row.rank_change !== 0 && (
            <span style={{
              fontSize: 11,
              fontWeight: 700,
              fontFamily: 'var(--font-ui)',
              color: row.rank_change > 0 ? '#22c55e' : '#f87171',
              display: 'flex',
              alignItems: 'center',
              gap: 1,
            }}>
              {row.rank_change > 0 ? '↑' : '↓'}{Math.abs(row.rank_change)}
            </span>
          )}
          {row.rank_change === 0 && (
            <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.2)', fontFamily: 'var(--font-ui)' }}>—</span>
          )}
        </div>
      </Td>
      <Td>{row.team_name || "Unnamed Team"}</Td>
      <Td>{row.user_id || "-"}</Td>
      <Td>
        <SpringNumber
          value={row.total_points ?? 0}
          className="num-lg"
        />
      </Td>
      <Td><span className="num-md">{row.squad_size ?? 0}</span></Td>
      <Td>
        <SpringNumber
          value={row.budget_left ?? 0}
          className="num-lg"
        />
      </Td>
    </tr>
  );
}

const forfeitedBannerStyle: React.CSSProperties = {
  background: "rgba(239, 68, 68, 0.05)",
  backdropFilter: "blur(12px)",
  border: "1px solid rgba(239, 68, 68, 0.35)",
  borderRadius: 16,
  padding: "16px 20px",
  display: "flex",
  alignItems: "center",
  gap: 14,
  color: "#f87171",
  fontFamily: "var(--font-ui)",
  boxShadow: "0 8px 32px rgba(0,0,0,0.2)",
};