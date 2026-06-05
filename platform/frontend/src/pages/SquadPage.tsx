import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { API_BASE } from "@/services/api";
import { FlagImg } from "@/components/FlagImg";
import { EmptyState } from "@/components/ui/EmptyState";

type SquadRow = {
  player?: {
    id?: string;
    position?: string;
    name?: string;
    club?: string;
    flag_code?: string;
    goals_2526?: number;
    assists_2526?: number;
    minutes_2526?: number;
    form_score?: number;
  };
  purchase_price?: number;
  player_total_points?: number;
  in_best_xi?: boolean;
};

type LeagueMember = {
  user_id: string;
  team_name?: string;
  total_points?: number;
};

function sectionLabel(position: string): string {
  const map: Record<string, string> = {
    GK: "GOALKEEPERS",
    DEF: "DEFENDERS",
    MID: "MIDFIELDERS",
    FWD: "FORWARDS",
  };
  return map[position] || position;
}

function barWidth(value?: number): string {
  const safe = Math.max(0, Math.min(100, Number(value ?? 0)));
  return `${safe}%`;
}

export default function SquadPage() {
  const { id = "", uid = "" } = useParams();
  const [squad, setSquad] = useState<SquadRow[]>([]);
  const [member, setMember] = useState<LeagueMember | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    async function loadSquad() {
      setLoading(true);
      setError("");
      try {
        const [leagueRes, squadRes] = await Promise.all([
          fetch(`${API_BASE}/api/v1/leagues/${id}`),
          fetch(`${API_BASE}/api/v1/leagues/${id}/squad/${uid}`),
        ]);
        const leagueData = await leagueRes.json();
        const squadData = await squadRes.json();
        if (!leagueRes.ok) throw new Error(leagueData.detail ?? "Failed to load league");
        if (!squadRes.ok) throw new Error(squadData.detail ?? "Failed to load squad");
        if (!active) return;
        const members = Array.isArray(leagueData.members) ? leagueData.members : [];
        setMember(members.find((entry: LeagueMember) => entry.user_id === uid) ?? null);
        setSquad(Array.isArray(squadData.squad) ? squadData.squad : []);
      } catch (error: unknown) {
        if (!active) return;
        setError(error instanceof Error ? error.message : String(error));
      } finally {
        if (active) setLoading(false);
      }
    }
    loadSquad();
    return () => {
      active = false;
    };
  }, [id, uid]);

  const byPos = useMemo(() => {
    const grouped: Record<string, SquadRow[]> = { GK: [], DEF: [], MID: [], FWD: [] };
    squad.forEach((entry) => {
      const position = (entry.player?.position || "").toUpperCase();
      if (grouped[position]) grouped[position].push(entry);
    });
    return grouped;
  }, [squad]);

  return (
    <div className="page-container" style={{ display: "grid", gap: 18 }}>
      <section className="wc-card section-card" style={{ padding: 24, display: "grid", gap: 10 }}>
        <div className="eyebrow">Squad overview</div>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 16, flexWrap: "wrap", alignItems: "flex-end" }}>
          <div style={{ display: "grid", gap: 4 }}>
            <h1 className="page-title" style={{ fontSize: "clamp(2rem, 4vw, 3rem)", marginBottom: 0 }}>{member?.team_name || "Squad"}</h1>
            <p className="page-sub" style={{ maxWidth: 760, margin: 0 }}>Username {uid} · {member?.total_points ?? 0} total points</p>
          </div>
          <div style={{ fontFamily: "var(--font-display)", fontSize: 28, fontWeight: 700, color: "#fff" }}>{member?.total_points ?? 0}</div>
        </div>
      </section>

      {/* Best XI explanation note */}
      <section style={{
        background: "rgba(167,139,250,0.06)",
        border: "1px solid rgba(167,139,250,0.25)",
        borderRadius: 14,
        padding: "14px 18px",
        display: "flex",
        alignItems: "center",
        gap: 12,
        fontSize: 13,
        color: "rgba(255,255,255,0.8)",
        fontFamily: "var(--font-ui)",
      }}>
        <span style={{ fontSize: 18 }}>⚽</span>
        <span>
          <strong style={{ color: "#a78bfa" }}>Best XI scoring:</strong>{" "}
          Only your top <strong>1 GK · 4 DEF · 3 MID · 3 FWD</strong> contribute to your team points each match cycle.
          Individual player points always accumulate — the best 11 are automatically selected.
          Players currently in your Best XI are marked with <strong style={{ color: "#22c55e" }}>✦ XI</strong>.
        </span>
      </section>

      {error && <div style={{ color: "#f87171", fontSize: 13 }}>{error}</div>}
      {loading ? (
        <section className="wc-card" style={{ padding: 24 }}>Loading squad...</section>
      ) : squad.length === 0 ? (
        <EmptyState
          icon="🪑"
          title="No squad yet"
          description="This manager has not bought any players yet. Head to the auction room to start building the squad."
        />
      ) : (
        <div style={{ display: "grid", gap: 18 }}>
          {(["GK", "DEF", "MID", "FWD"] as const).map((position) => {
            const players = byPos[position] || [];
            if (!players.length) return null;
            return (
              <section key={position} className="wc-card" style={{ padding: 20, display: "grid", gap: 14 }}>
                <div className="eyebrow">{sectionLabel(position)}</div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 14 }}>
                  {players.map((entry, index) => {
                    const player = entry.player ?? {};
                    const formScore = Number(player.form_score ?? 0);
                    const tournamentPts = entry.player_total_points ?? 0;
                    const inXI = entry.in_best_xi ?? false;
                    return (
                      <article key={`${player.name ?? position}-${index}`} className="wc-card" style={{
                        padding: 16,
                        display: "grid",
                        gap: 12,
                        borderTop: inXI ? "2px solid rgba(34,197,94,0.5)" : undefined,
                        background: inXI ? "rgba(34,197,94,0.03)" : undefined,
                      }}>
                        <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "flex-start" }}>
                          <div style={{ display: "flex", gap: 10, minWidth: 0 }}>
                            <FlagImg code={player.flag_code || "us"} size={22} />
                            <div style={{ display: "grid", gap: 4, minWidth: 0 }}>
                              <div style={{ display: "flex", alignItems: "center", gap: 7, flexWrap: "wrap" }}>
                                <div style={{ fontFamily: "var(--font-ui)", fontSize: 18, fontWeight: 700, color: "#fff", lineHeight: 1.1 }}>{player.name || "Unknown Player"}</div>
                                {inXI && (
                                  <span style={{
                                    fontSize: 10,
                                    fontWeight: 800,
                                    letterSpacing: "0.07em",
                                    color: "#22c55e",
                                    background: "rgba(34,197,94,0.12)",
                                    border: "1px solid rgba(34,197,94,0.3)",
                                    borderRadius: 6,
                                    padding: "2px 7px",
                                    fontFamily: "var(--font-ui)",
                                    whiteSpace: "nowrap",
                                  }}>✦ XI</span>
                                )}
                              </div>
                              <div style={{ color: "var(--color-text-secondary)", fontSize: 12 }}>{player.club || "Unknown club"}</div>
                            </div>
                          </div>
                          <div style={{ textAlign: "right", display: "grid", gap: 2 }}>
                            <div style={{ fontFamily: "var(--font-display)", fontSize: 20, fontWeight: 700, color: "#e3c15c" }}>{entry.purchase_price ?? 0}</div>
                            <div style={{ fontSize: 11, color: "rgba(255,255,255,0.45)", fontFamily: "var(--font-ui)" }}>paid</div>
                          </div>
                        </div>

                        {/* Tournament points */}
                        <div style={{
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "space-between",
                          background: "rgba(255,255,255,0.04)",
                          borderRadius: 10,
                          padding: "8px 12px",
                        }}>
                          <span style={{ fontSize: 11, fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: "rgba(255,255,255,0.5)", fontFamily: "var(--font-ui)" }}>
                            Tournament pts
                          </span>
                          <span style={{
                            fontFamily: "var(--font-display)",
                            fontSize: 20,
                            fontWeight: 800,
                            color: tournamentPts > 0 ? "#a78bfa" : tournamentPts < 0 ? "#f87171" : "rgba(255,255,255,0.3)",
                          }}>
                            {tournamentPts > 0 ? `+${tournamentPts}` : tournamentPts}
                          </span>
                        </div>

                        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: 10 }}>
                          <Stat label="Goals" value={String(player.goals_2526 ?? 0)} />
                          <Stat label="Assists" value={String(player.assists_2526 ?? 0)} />
                          <Stat label="Minutes" value={String(player.minutes_2526 ?? 0)} />
                        </div>

                        <div style={{ display: "grid", gap: 6 }}>
                          <div style={{ display: "flex", justifyContent: "space-between", gap: 12, fontSize: 11, fontWeight: 600, letterSpacing: "0.14em", textTransform: "uppercase", color: "rgba(212,175,55,0.75)" }}>
                            <span>Form score</span>
                            <span style={{ fontFamily: "var(--font-display)", fontSize: 18, color: "#fff" }}>{formScore}</span>
                          </div>
                          <div style={{ height: 3, borderRadius: 2, background: "rgba(255,255,255,0.08)", overflow: "hidden" }}>
                            <div style={{ width: barWidth(formScore), height: "100%", borderRadius: 2, background: formScore >= 70 ? "#22c55e" : formScore >= 40 ? "#facc15" : "#ef4444" }} />
                          </div>
                        </div>
                      </article>
                    );
                  })}
                </div>
              </section>
            );
          })}
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: "grid", gap: 4 }}>
      <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: "0.14em", textTransform: "uppercase", color: "rgba(212,175,55,0.75)" }}>{label}</div>
      <div style={{ fontFamily: "var(--font-display)", fontSize: 22, fontWeight: 700, color: "#fff", lineHeight: 1 }}>{value}</div>
    </div>
  );
}