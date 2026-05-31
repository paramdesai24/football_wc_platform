import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { API_BASE } from "@/services/api";
import { FlagImg } from "@/components/FlagImg";

type SquadRow = {
  player?: {
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

      {error && <div style={{ color: "#f87171", fontSize: 13 }}>{error}</div>}
      {loading ? (
        <section className="wc-card" style={{ padding: 24 }}>Loading squad...</section>
      ) : (
        <div style={{ display: "grid", gap: 18 }}>
          {(["GK", "DEF", "MID", "FWD"] as const).map((position) => {
            const players = byPos[position];
            if (!players.length) return null;
            return (
              <section key={position} className="wc-card" style={{ padding: 20, display: "grid", gap: 14 }}>
                <div className="eyebrow">{sectionLabel(position)}</div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 14 }}>
                  {players.map((entry, index) => {
                    const player = entry.player ?? {};
                    const formScore = Number(player.form_score ?? 0);
                    return (
                      <article key={`${player.name ?? position}-${index}`} className="wc-card" style={{ padding: 16, display: "grid", gap: 12 }}>
                        <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "flex-start" }}>
                          <div style={{ display: "flex", gap: 10, minWidth: 0 }}>
                            <FlagImg code={player.flag_code || "us"} size={22} />
                            <div style={{ display: "grid", gap: 4, minWidth: 0 }}>
                              <div style={{ fontFamily: "var(--font-ui)", fontSize: 18, fontWeight: 700, color: "#fff", lineHeight: 1.1 }}>{player.name || "Unknown Player"}</div>
                              <div style={{ color: "var(--color-text-secondary)", fontSize: 12 }}>{player.club || "Unknown club"}</div>
                            </div>
                          </div>
                          <div style={{ fontFamily: "var(--font-display)", fontSize: 24, fontWeight: 700, color: "#e3c15c" }}>{entry.purchase_price ?? 0}</div>
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