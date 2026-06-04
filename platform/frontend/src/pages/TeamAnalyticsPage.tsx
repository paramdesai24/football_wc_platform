/**
 * Team Analytics — mirrors render_analytics_page() from Streamlit app.py
 *
 * Layout:
 *   - Team selector (selectbox)
 *   - Fetch Analytics button
 *   - JSON response display from /api/v1/analytics/team/{team_id}
 */

import { useEffect, useMemo, useState } from "react";
import { apiGet } from "@/services/api";
import Sparkline from "@/components/charts/Sparkline";
import type { TeamAnalyticsResponse } from "@/contracts/analytics.contract";
import { FlagImg } from "@/components/FlagImg";
import { teamFlagCode } from "@/lib/flags";
import { smartScoreBar, ratingBar, formBar, momentumBar, consistencyBar } from "@/utils/statBar";

function getTeamCode(teamName: string, teamUid: string) {
  const prefixMatch = teamName.match(/^([A-Z]{2})\s+/i);
  const prefixCode = prefixMatch?.[1];
  if (prefixCode) return prefixCode.toUpperCase();

  const uidMatch = teamUid.match(/^C_([A-Z]{2})/i);
  const uidCode = uidMatch?.[1];
  if (uidCode) return uidCode.toUpperCase();

  return "";
}

function cleanTeamName(teamName: string) {
  return teamName.replace(/^[A-Z]{2}\s+/i, "").trim();
}

export default function TeamAnalyticsPage() {
  const [availableTeams, setAvailableTeams] = useState<{ country_name: string; country_uid: string }[]>([]);
  const [selectedUid, setSelectedUid] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<TeamAnalyticsResponse | null>(null);
  const [error, setError] = useState("");

  const selectedTeam = useMemo(
    () => availableTeams.find((team) => team.country_uid === selectedUid) ?? null,
    [availableTeams, selectedUid],
  );

  const trendPoints = useMemo(() => {
    const recent = Number(data?.recent_form ?? 0.5);
    const momentum = Number(data?.momentum ?? 0);
    return Array.from({ length: 8 }, (_, index) => {
      const progress = index / 7;
      const wave = Math.sin(progress * Math.PI) * momentum * 0.12;
      const drift = (progress - 0.5) * momentum * 0.18;
      return Math.max(0, Math.min(1, recent + wave + drift + (progress - 0.5) * 0.02));
    });
  }, [data]);

  useEffect(() => {
    // Fetch available teams from the backend rankings endpoint and populate dropdown
    apiGet<{ data?: { country_name: string; country_uid: string }[] }>("/api/v1/countries/rankings?limit=200").then((res) => {
      const rows = Array.isArray(res.data) ? res.data : (res.data as any)?.data;
      if (rows && rows.length > 0) {
        // Map to expected shape
        const teams = rows.map((r: any) => ({ country_name: r.country_name, country_uid: r.country_uid }));
        setAvailableTeams(teams);
        if (!selectedUid && teams.length > 0) setSelectedUid(teams[0].country_uid);
      }
    });
  }, []);

  const handleFetch = async () => {
    if (!selectedUid) return;
    setLoading(true);
    setData(null);
    setError("");
    const res = await apiGet<TeamAnalyticsResponse>(`/api/v1/analytics/team/${selectedUid}`);
    setLoading(false);

    if (res.error) {
      setError(`Analytics unavailable: ${res.error}`);
    } else if (res.data) {
      setData(res.data as TeamAnalyticsResponse);
    } else {
      setError("No analytics data returned for this team.");
    }
  };

  const metrics = data
    ? [
        { label: "Power Index", value: Math.round(data.power_index ?? 50.0), tone: "var(--color-accent)", fill: data.power_index ?? 50.0 },
        { label: "Smart Score (Elo)", value: Math.round(data.elo_rating), tone: "var(--color-accent)", fill: smartScoreBar(data.elo_rating) },
        { label: "Attack Rating", value: Math.round(data.attack_rating), tone: "var(--color-green)", fill: ratingBar(data.attack_rating) },
        { label: "Defense Rating", value: Math.round(data.defense_rating), tone: "var(--color-gold)", fill: ratingBar(data.defense_rating) },
      ]
    : [];

  return (
    <div className="page-content">
      <div className="wc-card section-card" style={{ marginBottom: 18 }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 18, alignItems: "flex-start", flexWrap: "wrap" }}>
          <div style={{ display: "grid", gap: 8 }}>
            <div className="eyebrow">Team analytics</div>
            <h1 className="page-title" style={{ fontSize: "1.75rem", marginBottom: 0 }}>Team intelligence</h1>
            <p className="page-sub" style={{ maxWidth: 760 }}>
              Pick a qualified team, then review its rating profile, recent form, and momentum.
            </p>
          </div>

          <div className="wc-card" style={{ minWidth: 260, maxWidth: 340, width: "100%", background: "var(--color-bg-raised)", padding: 20, display: "grid", gap: 8 }}>
            <div style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", marginBottom: 8 }}>Selected team</div>
            <div style={{ fontSize: "1.05rem", fontWeight: 800, marginBottom: 8 }}>
              {selectedTeam ? (
                <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
                  <FlagImg code={teamFlagCode(selectedTeam.country_uid) || getTeamCode(selectedTeam.country_name, selectedTeam.country_uid)} size={20} />
                  <span>{cleanTeamName(selectedTeam.country_name)}</span>
                </span>
              ) : (
                "Choose a team"
              )}
            </div>
            <div style={{ color: "var(--color-text-secondary)", fontSize: "0.85rem", lineHeight: 1.6 }}>
              {data ? `Elo Rank ${data.rank ?? "-"} · Power Rank ${data.power_rank ?? "-"} · ${data.confederation ?? "Unknown confederation"}` : "Load a team card to reveal the latest analytics bundle."}
            </div>
          </div>
        </div>
      </div>

      <div className="layout-hero-compact analytics-controls">
        <div className="wc-card" style={{ display: "grid", gap: 14, padding: "20px 24px" }}>
          <div className="analytics-field">
            <label className="field-label">Select team</label>
            <div className="field-row">
              <div className="ts-wrap">
                <select className="select ts-trigger" value={selectedUid} onChange={(e) => setSelectedUid(e.target.value)} style={{ width: "100%" }}>
                  {availableTeams.map((team) => {
                    return (
                      <option key={team.country_uid} value={team.country_uid}>
                        {cleanTeamName(team.country_name)}
                      </option>
                    );
                  })}
                </select>
              </div>

              <button className="fetch-btn" disabled={loading || !selectedUid} onClick={handleFetch}>
                {loading ? <><span className="spinner" /> Fetching...</> : "Fetch analytics"}
              </button>
            </div>
          </div>
        </div>

        <div className="wc-card section-card" style={{ display: "grid", gap: 10 }}>
          <div className="eyebrow">Form pulse</div>
          <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
            <div style={{ width: 180 }}>
              <Sparkline points={trendPoints.map((point) => point * 100)} width={180} height={48} stroke="var(--color-gold)" />
            </div>
            <div style={{ color: "var(--color-text-secondary)", fontSize: "0.85rem", lineHeight: 1.7, maxWidth: 360 }}>
              {data ? `Recent form: ${Math.round(data.recent_form * 100)}% · Momentum: ${Number(data.momentum).toFixed(2)}` : "Recent form and momentum update after loading a team."}
            </div>
          </div>
        </div>
      </div>

      {error && (
        <div className="card-compact" style={{ borderColor: "rgba(248,81,73,0.2)", color: "var(--color-red)", marginBottom: 12 }}>
          {error}
        </div>
      )}

      {data && (
        <div className="wc-card" style={{ padding: 18, display: "grid", gap: 16 }}>
          <div className="team-header">
            <div className="team-meta">
              <div className="team-name">
                <FlagImg code={getTeamCode(data.country_name, data.country_id)} size={20} />
                <span>{cleanTeamName(data.country_name)}</span>
              </div>
              <div className="team-sub">
                {data.confederation ?? "-"} · Elo Rank {data.rank ?? "-"} {data.power_rank ? `· Power Rank ${data.power_rank}` : ""}
              </div>
            </div>
            <div className="momentum-badge">
              Momentum <span>{Number(data.momentum).toFixed(2)}</span>
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16 }}>
            {metrics.map((item) => (
              <div key={item.label} className="wc-card stat-card">
                <div className="stat-card-top">
                  <div className="stat-label">{item.label}</div>
                  <div className="stat-value">{item.value}</div>
                </div>
                <div className="stat-bar-track">
                  <div
                    className="stat-bar-fill"
                    style={{
                      width: `${item.fill}%`,
                      backgroundColor: item.tone,
                      boxShadow: `0 0 10px ${item.tone}`,
                    }}
                  />
                </div>
              </div>
            ))}
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 12 }}>
            <div className="wc-card stat-card" style={{ flex: 1 }}>
              <div className="stat-label">Form (recent)</div>
              <div className="stat-value">{Math.round(data.recent_form * 100)}%</div>
              <div className="stat-bar-track">
                <div className="stat-bar-fill" style={{ width: `${formBar(data.recent_form)}%`, backgroundColor: "var(--color-accent)", boxShadow: "0 0 10px var(--color-accent)" }} />
              </div>
            </div>
            <div className="wc-card stat-card" style={{ flex: 1 }}>
              <div className="stat-label">Squad Strength</div>
              <div className="stat-value">{Math.round((data.squad_strength ?? 0) * 100)}%</div>
              <div className="stat-bar-track">
                <div className="stat-bar-fill" style={{ width: `${(data.squad_strength ?? 0) * 100}%`, backgroundColor: "var(--color-gold)", boxShadow: "0 0 10px var(--color-gold)" }} />
              </div>
            </div>
            <div className="wc-card stat-card" style={{ flex: 1 }}>
              <div className="stat-label">Momentum</div>
              <div className="stat-value">{Number(data.momentum).toFixed(2)}</div>
              <div className="stat-bar-track">
                <div
                  className="stat-bar-fill"
                  style={{
                    width: `${momentumBar(data.momentum)}%`,
                    backgroundColor: data.momentum >= 0 ? "var(--color-green)" : "var(--color-red)",
                    boxShadow: `0 0 10px ${data.momentum >= 0 ? "var(--color-green)" : "var(--color-red)"}`,
                  }}
                />
              </div>
            </div>
            <div className="wc-card stat-card" style={{ flex: 1 }}>
              <div className="stat-label">Consistency</div>
              <div className="stat-value">{Math.round(data.consistency * 100)}%</div>
              <div className="stat-bar-track">
                <div className="stat-bar-fill" style={{ width: `${consistencyBar(data.consistency)}%`, backgroundColor: "var(--color-gold)", boxShadow: "0 0 10px var(--color-gold)" }} />
              </div>
            </div>
          </div>

          {/* Detailed Component Breakdowns */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 20, marginTop: 16 }}>
            
            {/* Attack Profile */}
            <div className="wc-card" style={{ padding: 22, background: "rgba(10, 18, 34, 0.45)", border: "1px solid rgba(34,197,94,0.15)", borderRadius: 16, backdropFilter: "blur(12px)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, color: "#10b981", fontSize: "0.75rem", fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase" }}>
                <span style={{ width: 6, height: 6, borderRadius: "50%", backgroundColor: "#10b981" }} />
                Attacking Profile
              </div>
              <h3 style={{ fontSize: "1.25rem", fontWeight: 800, margin: "8px 0 16px 0", letterSpacing: "-0.015em", color: "#fff" }}>Offensive Metrics</h3>
              
              <div style={{ display: "grid", gap: 16 }}>
                {[
                  { label: "Scoring Frequency", val: data.attack_breakdown?.recency_attack ?? 0, desc: "Recent goalscoring rate adjusted for opponent quality" },
                  { label: "Squad Attacking Threat", val: data.attack_breakdown?.squad_attack ?? 0, desc: "Forward line market valuation & attacking depth" },
                  { label: "Quality Baseline", val: data.attack_breakdown?.elo_component ?? 0, desc: "Long-term historical baseline performance" },
                  { label: "Recent Momentum", val: data.attack_breakdown?.form_component ?? 0, desc: "Competitive record and fixture results trend" }
                ].map((comp) => (
                  <div key={comp.label}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "0.85rem", marginBottom: 4 }}>
                      <span style={{ fontWeight: 600, color: "rgba(255,255,255,0.9)" }}>{comp.label}</span>
                      <span style={{ background: "rgba(16,185,129,0.12)", color: "#34d399", padding: "2px 8px", borderRadius: 6, fontSize: "0.75rem", fontWeight: 700 }}>
                        {Math.round(comp.val)} pts
                      </span>
                    </div>
                    <div style={{ fontSize: "0.72rem", color: "rgba(255,255,255,0.45)", marginBottom: 6, lineHeight: 1.3 }}>{comp.desc}</div>
                    <div style={{ height: 6, borderRadius: 3, background: "rgba(255,255,255,0.06)", overflow: "hidden" }}>
                      <div style={{ width: `${comp.val}%`, height: "100%", background: "linear-gradient(90deg, #10b981, #34d399)", borderRadius: 3, boxShadow: "0 0 8px rgba(16,185,129,0.4)" }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Defense Profile */}
            <div className="wc-card" style={{ padding: 22, background: "rgba(10, 18, 34, 0.45)", border: "1px solid rgba(212,175,55,0.15)", borderRadius: 16, backdropFilter: "blur(12px)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, color: "#d4af37", fontSize: "0.75rem", fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase" }}>
                <span style={{ width: 6, height: 6, borderRadius: "50%", backgroundColor: "#d4af37" }} />
                Defensive Solidity Profile
              </div>
              <h3 style={{ fontSize: "1.25rem", fontWeight: 800, margin: "8px 0 16px 0", letterSpacing: "-0.015em", color: "#fff" }}>Defensive Metrics</h3>
              
              <div style={{ display: "grid", gap: 16 }}>
                {[
                  { label: "Goals Conceded Efficiency", val: data.defense_breakdown?.defensive_record ?? 0, desc: "Goals conceded record weighted against opponent quality" },
                  { label: "Backline Market Depth", val: data.defense_breakdown?.defender_quality ?? 0, desc: "Market value and elite league representations of defenders" },
                  { label: "Shot-Stopping Skill", val: data.defense_breakdown?.goalkeeper_quality ?? 0, desc: "Active goalkeeper save percentage & caps rating" },
                  { label: "Shutout Consistency", val: data.defense_breakdown?.clean_sheet_component ?? 0, desc: "Frequency of recent clean sheets in competitive fixtures" }
                ].map((comp) => (
                  <div key={comp.label}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "0.85rem", marginBottom: 4 }}>
                      <span style={{ fontWeight: 600, color: "rgba(255,255,255,0.9)" }}>{comp.label}</span>
                      <span style={{ background: "rgba(212,175,55,0.12)", color: "#f7d774", padding: "2px 8px", borderRadius: 6, fontSize: "0.75rem", fontWeight: 700 }}>
                        {Math.round(comp.val)} pts
                      </span>
                    </div>
                    <div style={{ fontSize: "0.72rem", color: "rgba(255,255,255,0.45)", marginBottom: 6, lineHeight: 1.3 }}>{comp.desc}</div>
                    <div style={{ height: 6, borderRadius: 3, background: "rgba(255,255,255,0.06)", overflow: "hidden" }}>
                      <div style={{ width: `${comp.val}%`, height: "100%", background: "linear-gradient(90deg, #d4af37, #f7d774)", borderRadius: 3, boxShadow: "0 0 8px rgba(212,175,55,0.4)" }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

          </div>
        </div>
      )}

      {!data && !error && !loading && (
        <div className="card-compact" style={{ color: "var(--color-accent)" }}>
          ℹ Select a team and click Fetch Analytics to view data.
        </div>
      )}
    </div>
  );
}
