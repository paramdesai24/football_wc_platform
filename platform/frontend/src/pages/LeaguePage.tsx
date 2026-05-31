import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { API_BASE } from "@/services/api";
import { EmptyState } from "@/components/ui/EmptyState";

type LeagueMember = {
  user_id: string;
  team_name?: string;
  budget_left?: number;
  total_points?: number;
  squad_count?: number;
};

type LeagueData = {
  name?: string;
  status?: string;
  budget?: number;
  squad_size?: number;
  invite_code?: string;
};

function statusBadge(status: string | undefined): React.CSSProperties {
  const value = (status || "").toLowerCase();
  const colors: Record<string, React.CSSProperties> = {
    auction: { background: "rgba(212,175,55,0.14)", color: "#e3c15c", border: "1px solid rgba(212,175,55,0.28)" },
    active: { background: "rgba(34,197,94,0.12)", color: "#7ee2a8", border: "1px solid rgba(34,197,94,0.24)" },
    completed: { background: "rgba(148,163,184,0.12)", color: "#cbd5e1", border: "1px solid rgba(148,163,184,0.22)" },
  };
  return {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    minHeight: 26,
    padding: "0 10px",
    borderRadius: 999,
    fontSize: 10,
    fontWeight: 700,
    letterSpacing: "0.14em",
    textTransform: "uppercase",
    fontFamily: "var(--font-ui)",
    ...(colors[value] ?? { background: "rgba(255,255,255,0.08)", color: "rgba(255,255,255,0.75)", border: "1px solid rgba(255,255,255,0.1)" }),
  };
}

function formatPercent(value: number): string {
  if (!Number.isFinite(value)) return "0%";
  return `${Math.max(0, Math.min(100, value)).toFixed(0)}%`;
}

function buttonLink(primary: boolean): React.CSSProperties {
  return {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "8px 14px",
    borderRadius: 8,
    fontWeight: 700,
    textDecoration: "none",
    fontSize: 13,
    ...(primary
      ? { background: "linear-gradient(90deg,#2563eb,#7c3aed)", color: "#fff", border: "1px solid rgba(255,255,255,0.06)" }
      : { background: "transparent", color: "rgba(255,255,255,0.9)", border: "1px solid rgba(255,255,255,0.06)" }),
  } as React.CSSProperties;
}

function Stat({ label, value, suffix }: { label: string; value: string; suffix?: string }) {
  return (
    <div style={{ display: "grid", gap: 6 }}>
      <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: "0.14em", textTransform: "uppercase", color: "var(--color-text-secondary)" }}>{label}</div>
      <div style={{ fontFamily: "var(--font-display)", fontWeight: 700, color: "#fff" }}>{value}{suffix ? <span style={{ color: "var(--color-text-secondary)", fontWeight: 400, marginLeft: 6 }}>{suffix}</span> : null}</div>
    </div>
  );
}

export default function LeaguePage() {
  const { id = "" } = useParams();
  const [league, setLeague] = useState<LeagueData | null>(null);
  const [members, setMembers] = useState<LeagueMember[]>([]);
  const [memberCount, setMemberCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    async function loadLeague() {
      setLoading(true);
      setError("");
      try {
        const res = await fetch(`${API_BASE}/api/v1/leagues/${id}`);
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail ?? "Failed to load league");
        if (!active) return;
        setLeague(data.league ?? null);
        setMembers(Array.isArray(data.members) ? data.members : []);
        setMemberCount(Number(data.member_count ?? 0));
      } catch (error: unknown) {
        if (!active) return;
        setError(error instanceof Error ? error.message : String(error));
      } finally {
        if (active) setLoading(false);
      }
    }
    loadLeague();
    return () => {
      active = false;
    };
  }, [id]);

  const maxBudget = Math.max(league?.budget ?? 0, 1);

  return (
    <div className="page-container" style={{ display: "grid", gap: 18 }}>
      <section className="wc-card section-card" style={{ padding: 24, display: "grid", gap: 12 }}>
        <div className="eyebrow">League overview</div>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 16, alignItems: "flex-start", flexWrap: "wrap" }}>
          <div style={{ display: "grid", gap: 6 }}>
            <h1 className="page-title" style={{ fontSize: "clamp(2rem, 4vw, 3rem)", marginBottom: 0 }}>{league?.name || `League ${id}`}</h1>
            <p className="page-sub" style={{ maxWidth: 760, margin: 0 }}>
              Track member budgets, squad sizes, and total points from the league hub.
            </p>
          </div>
          <span style={statusBadge(league?.status)}>{league?.status || "loading"}</span>
        </div>

        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
          <div style={{ color: "rgba(255,255,255,0.72)", fontSize: 13 }}><strong style={{ color: "#fff" }}>{memberCount}</strong> members</div>
          <div style={{ color: "rgba(255,255,255,0.72)", fontSize: 13 }}><strong style={{ color: "#fff" }}>Budget</strong> {league?.budget ?? 0}</div>
          {league?.invite_code && <div style={{ color: "rgba(255,255,255,0.72)", fontSize: 13 }}><strong style={{ color: "#fff" }}>Invite</strong> {league.invite_code}</div>}
        </div>

        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
          <Link to={`/league/${id}/leaderboard`} style={buttonLink(true)}>View Leaderboard</Link>
          <Link to={`/auction/room/${id}`} style={buttonLink(false)}>Enter Auction Room</Link>
        </div>
      </section>

      {error && <div style={{ color: "#f87171", fontSize: 13 }}>{error}</div>}

      {loading ? (
        <section className="wc-card" style={{ padding: 24 }}>Loading league data...</section>
      ) : members.length <= 1 ? (
        <EmptyState
          icon="👤"
          title="Waiting for league members"
          description="Only the host is in this league so far. Share the invite code to get more managers into the auction."
        />
      ) : (
        <section style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 16 }}>
          {members.map((member) => {
            const budgetLeft = Number(member.budget_left ?? 0);
            const percent = (budgetLeft / maxBudget) * 100;
            const barColor = percent > 50 ? "#22c55e" : percent >= 20 ? "#facc15" : "#ef4444";
            return (
              <article key={member.user_id} className="wc-card" style={{ padding: 20, display: "grid", gap: 14 }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 10, alignItems: "flex-start" }}>
                  <div style={{ display: "grid", gap: 4, minWidth: 0 }}>
                    <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: "0.14em", textTransform: "uppercase", color: "rgba(212,175,55,0.75)" }}>Team</div>
                    <div style={{ fontFamily: "var(--font-ui)", fontSize: 20, fontWeight: 700, color: "#fff", overflow: "hidden", textOverflow: "ellipsis" }}>{member.team_name || "Unnamed Team"}</div>
                  </div>
                  <div style={{ fontSize: 12, color: "var(--color-text-secondary)" }}>{member.user_id}</div>
                </div>

                <div style={{ display: "grid", gap: 6 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 12, color: "var(--color-text-secondary)", fontSize: 12 }}>
                    <span>Budget left</span>
                    <span style={{ fontFamily: "var(--font-display)", fontWeight: 700, color: "#fff" }}>{budgetLeft}</span>
                  </div>
                  <div style={{ height: 3, borderRadius: 2, background: "rgba(255,255,255,0.08)", overflow: "hidden" }}>
                    <div style={{ width: formatPercent(percent), height: "100%", background: barColor, borderRadius: 2 }} />
                  </div>
                </div>

                <div style={{ display: "flex", gap: 14, flexWrap: "wrap", alignItems: "center" }}>
                  <Stat label="Squad size" value={String(member.squad_count ?? 0)} suffix={`/ ${league?.squad_size ?? 0}`} />
                  <Stat label="Total points" value={String(member.total_points ?? 0)} />
                </div>

                <Link to={`/league/${id}/squad/${member.user_id}`} style={buttonLink(false)}>
                  View Squad →
                </Link>
              </article>
            );
          })}
        </section>
      )}
    </div>
  );
}