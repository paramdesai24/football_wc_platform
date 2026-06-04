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
    apiGet<{ data?: { country_name: string; country_uid: string }[] }>("/api/v1/countries/?limit=200").then((res) => {
      const rows = Array.isArray(res.data) ? res.data : (res.data as any)?.data;
      if (rows && rows.length > 0) {
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
        { label: "Smart Score", value: data.overall_rank_score != null ? `${Math.round(data.overall_rank_score * 100)}%` : "—", tone: "#d4af37", fill: data.overall_rank_score != null ? data.overall_rank_score * 100 : 50, shadow: "rgba(212, 175, 55, 0.3)" },
        { label: "Elo Rating", value: Math.round(data.elo_rating), tone: "#a78bfa", fill: smartScoreBar(data.elo_rating), shadow: "rgba(167, 139, 250, 0.3)" },
        { label: "Power Index", value: Math.round(data.power_index ?? 50.0), tone: "#f43f5e", fill: data.power_index ?? 50.0, shadow: "rgba(244, 63, 94, 0.3)" },
        { label: "Attack Rating", value: Math.round(data.attack_rating), tone: "#10b981", fill: ratingBar(data.attack_rating), shadow: "rgba(16, 185, 129, 0.3)" },
        { label: "Defense Rating", value: Math.round(data.defense_rating), tone: "#3b82f6", fill: ratingBar(data.defense_rating), shadow: "rgba(59, 130, 246, 0.3)" },
      ]
    : [];

  return (
    <div className="page-content page-fade">
      {/* Upper header block */}
      <div className="wc-card section-card" style={{ marginBottom: 18, background: "linear-gradient(135deg, rgba(10, 18, 34, 0.85) 0%, rgba(18, 28, 49, 0.6) 100%)", border: "1px solid rgba(255, 255, 255, 0.08)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 18, alignItems: "center", flexWrap: "wrap" }}>
          <div style={{ display: "grid", gap: 6 }}>
            <div className="eyebrow" style={{ color: "var(--color-accent)", letterSpacing: "0.15em", fontWeight: 700 }}>Team analytics</div>
            <h1 className="page-title" style={{ fontSize: "2rem", marginBottom: 2, fontWeight: 800, color: "#fff", fontFamily: "var(--font-ui)", letterSpacing: "-0.02em" }}>Team Intelligence</h1>
            <p className="page-sub" style={{ maxWidth: 760, color: "var(--color-text-secondary)", fontSize: "0.9rem", lineHeight: 1.5 }}>
              Analyze and compare qualified national squads, form metrics, Elo history, and defensive/offensive solidities.
            </p>
          </div>

          <div className="wc-card" style={{ minWidth: 280, maxWidth: 360, width: "100%", background: "rgba(5, 10, 20, 0.45)", border: "1px solid rgba(255,255,255,0.06)", padding: "16px 20px", display: "grid", gap: 8, borderRadius: 12 }}>
            <div style={{ fontSize: "0.72rem", color: "var(--color-text-muted)", textTransform: "uppercase", fontWeight: 700, letterSpacing: "0.06em" }}>Selected team</div>
            <div style={{ fontSize: "1.2rem", fontWeight: 800, color: "#fff", display: "flex", alignItems: "center", gap: 10 }}>
              {selectedTeam ? (
                <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
                  <FlagImg code={teamFlagCode(selectedTeam.country_uid) || getTeamCode(selectedTeam.country_name, selectedTeam.country_uid)} size={24} style={{ borderRadius: 3, border: "1px solid rgba(255,255,255,0.1)" }} />
                  <span>{cleanTeamName(selectedTeam.country_name)}</span>
                </span>
              ) : (
                "Choose a team"
              )}
            </div>
            <div style={{ color: "var(--color-text-secondary)", fontSize: "0.8rem", lineHeight: 1.4, borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: 8, marginTop: 2 }}>
              {data ? (
                <span style={{ display: "flex", flexWrap: "wrap", gap: "4px 8px" }}>
                  <span>Elo Rank <strong style={{ color: "#fff" }}>#{data.rank ?? "-"}</strong></span>
                  <span style={{ color: "rgba(255,255,255,0.2)" }}>•</span>
                  <span>Power Rank <strong style={{ color: "#fff" }}>#{data.power_rank ?? "-"}</strong></span>
                  <span style={{ color: "rgba(255,255,255,0.2)" }}>•</span>
                  <span style={{ color: "var(--color-accent)" }}>{data.confederation}</span>
                </span>
              ) : "Load a team card to reveal the latest analytics bundle."}
            </div>
          </div>
        </div>
      </div>

      {/* Control bar + Sparkline */}
      <div className="layout-hero-compact analytics-controls" style={{ marginBottom: 20, display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 18 }}>
        {/* Dropdown Card */}
        <div className="wc-card" style={{ display: "flex", flexDirection: "column", gap: 12, padding: "20px 24px", justifyContent: "center" }}>
          <label className="field-label" style={{ fontSize: "0.72rem", color: "var(--color-text-muted)", textTransform: "uppercase", fontWeight: 700, letterSpacing: "0.08em", marginBottom: 2 }}>Select national team</label>
          <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
            <div style={{ flex: 1, position: "relative" }}>
              <select 
                className="select" 
                value={selectedUid} 
                onChange={(e) => setSelectedUid(e.target.value)} 
                style={{ 
                  width: "100%",
                  height: "44px",
                  background: "rgba(255, 255, 255, 0.04)",
                  border: "1px solid rgba(255, 255, 255, 0.08)",
                  borderRadius: "10px",
                  color: "#fff",
                  padding: "0 16px",
                  fontSize: "0.95rem",
                  fontWeight: 600,
                  outline: "none",
                  cursor: "pointer",
                  transition: "border-color 0.2s, background-color 0.2s"
                }}
              >
                {availableTeams.map((team) => (
                  <option key={team.country_uid} value={team.country_uid}>
                    {cleanTeamName(team.country_name)}
                  </option>
                ))}
              </select>
            </div>

            <button 
              className="fetch-btn" 
              disabled={loading || !selectedUid} 
              onClick={handleFetch}
              style={{
                height: "44px",
                background: "linear-gradient(135deg, #d4af37 0%, #aa8410 100%)",
                boxShadow: "0 4px 14px rgba(212, 175, 55, 0.25)",
                color: "#050d1a",
                fontWeight: 700,
                fontSize: "0.85rem",
                letterSpacing: "0.05em",
                textTransform: "uppercase",
                borderRadius: "10px",
                padding: "0 22px",
                border: "none",
                cursor: "pointer",
                transition: "transform 0.2s, opacity 0.2s",
                display: "inline-flex",
                alignItems: "center",
                gap: 8
              }}
            >
              {loading ? (
                <>
                  <span className="spinner" style={{ borderLeftColor: "#050d1a", width: 14, height: 14 }} />
                  Loading
                </>
              ) : "Fetch metrics"}
            </button>
          </div>
        </div>

        {/* Sparkline Card */}
        <div className="wc-card" style={{ display: "flex", alignItems: "center", gap: 20, padding: "20px 24px" }}>
          <div style={{ display: "grid", gap: 4 }}>
            <div className="eyebrow" style={{ color: "var(--color-accent)", letterSpacing: "0.1em", fontWeight: 700, fontSize: "0.7rem" }}>Recent Form Trend</div>
            <div style={{ color: "#fff", fontSize: "1.1rem", fontWeight: 800 }}>Form Pulse Index</div>
            <div style={{ color: "var(--color-text-secondary)", fontSize: "0.82rem", lineHeight: 1.4, maxWidth: 220 }}>
              {data ? `Index: ${Math.round(data.recent_form * 100)}% · Momentum: ${Number(data.momentum).toFixed(2)}` : "Select a team to load the live form waveform index."}
            </div>
          </div>
          <div style={{ flex: 1, display: "flex", justifyContent: "center", alignItems: "center", minWidth: 120 }}>
            <Sparkline points={trendPoints.map((point) => point * 100)} width={180} height={52} stroke="var(--color-gold)" />
          </div>
        </div>
      </div>

      {error && (
        <div className="wc-card" style={{ borderColor: "rgba(239,68,68,0.2)", background: "rgba(239,68,68,0.06)", color: "#ef4444", marginBottom: 18, borderRadius: 12, padding: "14px 18px", fontSize: "0.9rem", display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: "1.2rem" }}>⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {data && (
        <div className="wc-card card-enter" style={{ padding: "20px 22px", display: "grid", gap: 20, border: "1px solid rgba(255,255,255,0.08)", boxShadow: "0 15px 35px rgba(0,0,0,0.4)", borderRadius: 16 }}>
          {/* Header Row of fetched details */}
          <div className="analytics-team-header" style={{ paddingBottom: 16 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap" }}>
              <FlagImg code={teamFlagCode(data.country_id) || getTeamCode(data.country_name, data.country_id)} size={44} style={{ borderRadius: 6, border: "2px solid rgba(255,255,255,0.15)", boxShadow: "0 4px 10px rgba(0,0,0,0.3)" }} />
              <div>
                <h2 style={{ fontSize: "2.1rem", fontWeight: 800, color: "#fff", margin: 0, letterSpacing: "-0.03em", fontFamily: "var(--font-ui)", lineHeight: 1.1, display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
                  <span>{cleanTeamName(data.country_name)}</span>
                  <span style={{ 
                    background: data.momentum >= 0 ? "rgba(16,185,129,0.1)" : "rgba(239,68,68,0.1)", 
                    border: `1px solid ${data.momentum >= 0 ? "rgba(16,185,129,0.25)" : "rgba(239,68,68,0.25)"}`, 
                    color: data.momentum >= 0 ? "#10b981" : "#ef4444", 
                    fontWeight: 800, 
                    fontSize: "12px",
                    padding: "3px 8px",
                    borderRadius: "6px",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: 4
                  }}>
                    {data.momentum >= 0 ? "▲" : "▼"} {Number(data.momentum).toFixed(2)}
                  </span>
                </h2>
                <div style={{ fontSize: "0.82rem", color: "var(--color-text-muted)", marginTop: 6, display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
                  <span className="wc-badge" style={{ background: "rgba(212,175,55,0.12)", border: "1px solid rgba(212,175,55,0.25)", color: "var(--color-accent)", padding: "2px 8px", borderRadius: 4, fontSize: "0.72rem", fontWeight: 700 }}>
                    {data.confederation}
                  </span>
                  <span style={{ color: "rgba(255,255,255,0.15)" }}>|</span>
                  <span>Elo Rank <strong style={{ color: "#fff" }}>#{data.rank}</strong></span>
                  {data.power_rank ? (
                    <>
                      <span style={{ color: "rgba(255,255,255,0.15)" }}>|</span>
                      <span>Power Rank <strong style={{ color: "#fff" }}>#{data.power_rank}</strong></span>
                    </>
                  ) : null}
                </div>
              </div>
            </div>
          </div>

          {/* Primary stats row */}
          <div className="analytics-metrics-grid">
            {metrics.map((item) => (
              <div 
                key={item.label} 
                className="analytics-stat-card"
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 6 }}>
                  <div style={{ fontSize: "0.72rem", fontWeight: 700, color: "var(--color-text-muted)", textTransform: "uppercase", letterSpacing: "0.04em" }}>{item.label}</div>
                  <div style={{ fontSize: "1.65rem", fontWeight: 800, color: "#fff", fontFamily: "var(--font-display)" }}>{item.value}</div>
                </div>
                <div className="stat-bar-track" style={{ height: 6, borderRadius: 3, background: "rgba(255,255,255,0.06)", overflow: "hidden", position: "relative" }}>
                  <div
                    className="stat-bar-fill"
                    style={{
                      width: `${item.fill}%`,
                      height: "100%",
                      backgroundColor: item.tone,
                      boxShadow: `0 0 10px ${item.shadow}`,
                      borderRadius: 3,
                      transition: "width 0.8s cubic-bezier(0.4, 0, 0.2, 1)",
                    }}
                  />
                </div>
              </div>
            ))}
          </div>

          {/* Secondary Stats Row */}
          <div className="analytics-secondary-grid">
            {/* Form */}
            <div className="analytics-stat-card">
              <div style={{ fontSize: "0.72rem", fontWeight: 700, color: "var(--color-text-muted)", textTransform: "uppercase", letterSpacing: "0.04em", marginBottom: 6 }}>Form (recent)</div>
              <div style={{ fontSize: "1.45rem", fontWeight: 800, color: "#fff", fontFamily: "var(--font-display)", marginBottom: 6 }}>{Math.round(data.recent_form * 100)}%</div>
              <div style={{ height: 4, borderRadius: 2, background: "rgba(255,255,255,0.06)", overflow: "hidden" }}>
                <div style={{ height: "100%", width: `${formBar(data.recent_form)}%`, backgroundColor: "var(--color-accent)", boxShadow: "0 0 8px rgba(212,175,55,0.4)" }} />
              </div>
            </div>

            {/* Squad Strength */}
            <div className="analytics-stat-card">
              <div style={{ fontSize: "0.72rem", fontWeight: 700, color: "var(--color-text-muted)", textTransform: "uppercase", letterSpacing: "0.04em", marginBottom: 6 }}>Squad Strength</div>
              <div style={{ fontSize: "1.45rem", fontWeight: 800, color: "#fff", fontFamily: "var(--font-display)", marginBottom: 6 }}>{Math.round((data.squad_strength ?? 0) * 100)}%</div>
              <div style={{ height: 4, borderRadius: 2, background: "rgba(255,255,255,0.06)", overflow: "hidden" }}>
                <div style={{ height: "100%", width: `${(data.squad_strength ?? 0) * 100}%`, backgroundColor: "#a78bfa", boxShadow: "0 0 8px rgba(167,139,250,0.4)" }} />
              </div>
            </div>

            {/* Momentum */}
            <div className="analytics-stat-card">
              <div style={{ fontSize: "0.72rem", fontWeight: 700, color: "var(--color-text-muted)", textTransform: "uppercase", letterSpacing: "0.04em", marginBottom: 6 }}>Momentum</div>
              <div style={{ fontSize: "1.45rem", fontWeight: 800, color: "#fff", fontFamily: "var(--font-display)", marginBottom: 6 }}>{Number(data.momentum).toFixed(2)}</div>
              <div style={{ height: 4, borderRadius: 2, background: "rgba(255,255,255,0.06)", overflow: "hidden" }}>
                <div
                  style={{
                    height: "100%",
                    width: `${momentumBar(data.momentum)}%`,
                    backgroundColor: data.momentum >= 0 ? "#10b981" : "#ef4444",
                    boxShadow: `0 0 8px ${data.momentum >= 0 ? "rgba(16,185,129,0.4)" : "rgba(239,68,68,0.4)"}`,
                  }}
                />
              </div>
            </div>

            {/* Consistency */}
            <div className="analytics-stat-card">
              <div style={{ fontSize: "0.72rem", fontWeight: 700, color: "var(--color-text-muted)", textTransform: "uppercase", letterSpacing: "0.04em", marginBottom: 6 }}>Consistency</div>
              <div style={{ fontSize: "1.45rem", fontWeight: 800, color: "#fff", fontFamily: "var(--font-display)", marginBottom: 6 }}>{Math.round(data.consistency * 100)}%</div>
              <div style={{ height: 4, borderRadius: 2, background: "rgba(255,255,255,0.06)", overflow: "hidden" }}>
                <div style={{ height: "100%", width: `${consistencyBar(data.consistency)}%`, backgroundColor: "#f59e0b", boxShadow: "0 0 8px rgba(245,158,11,0.4)" }} />
              </div>
            </div>
          </div>

          {/* Component Breakdowns */}
          <div className="analytics-breakdowns-grid" style={{ marginTop: 10 }}>
            {/* Attack Profile */}
            <div className="wc-card" style={{ padding: 24, background: "rgba(10, 18, 34, 0.45)", border: "1px solid rgba(16,185,129,0.15)", borderRadius: 16, backdropFilter: "blur(12px)", boxShadow: "0 8px 24px rgba(0,0,0,0.2)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, color: "#10b981", fontSize: "0.72rem", fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase" }}>
                <span style={{ width: 6, height: 6, borderRadius: "50%", backgroundColor: "#10b981" }} />
                Attacking Profile
              </div>
              <h3 style={{ fontSize: "1.35rem", fontWeight: 800, margin: "8px 0 18px 0", letterSpacing: "-0.015em", color: "#fff", fontFamily: "var(--font-ui)" }}>Offensive Metrics</h3>
              
              <div style={{ display: "grid", gap: 18 }}>
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
            <div className="wc-card" style={{ padding: 24, background: "rgba(10, 18, 34, 0.45)", border: "1px solid rgba(59,130,246,0.15)", borderRadius: 16, backdropFilter: "blur(12px)", boxShadow: "0 8px 24px rgba(0,0,0,0.2)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, color: "#3b82f6", fontSize: "0.72rem", fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase" }}>
                <span style={{ width: 6, height: 6, borderRadius: "50%", backgroundColor: "#3b82f6" }} />
                Defensive Solidity Profile
              </div>
              <h3 style={{ fontSize: "1.35rem", fontWeight: 800, margin: "8px 0 18px 0", letterSpacing: "-0.015em", color: "#fff", fontFamily: "var(--font-ui)" }}>Defensive Metrics</h3>
              
              <div style={{ display: "grid", gap: 18 }}>
                {[
                  { label: "Goals Conceded Efficiency", val: data.defense_breakdown?.defensive_record ?? 0, desc: "Goals conceded record weighted against opponent quality" },
                  { label: "Backline Market Depth", val: data.defense_breakdown?.defender_quality ?? 0, desc: "Market value and elite league representations of defenders" },
                  { label: "Shot-Stopping Skill", val: data.defense_breakdown?.goalkeeper_quality ?? 0, desc: "Active goalkeeper save percentage & caps rating" },
                  { label: "Shutout Consistency", val: data.defense_breakdown?.clean_sheet_component ?? 0, desc: "Frequency of recent clean sheets in competitive fixtures" }
                ].map((comp) => (
                  <div key={comp.label}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "0.85rem", marginBottom: 4 }}>
                      <span style={{ fontWeight: 600, color: "rgba(255,255,255,0.9)" }}>{comp.label}</span>
                      <span style={{ background: "rgba(59,130,246,0.12)", color: "#60a5fa", padding: "2px 8px", borderRadius: 6, fontSize: "0.75rem", fontWeight: 700 }}>
                        {Math.round(comp.val)} pts
                      </span>
                    </div>
                    <div style={{ fontSize: "0.72rem", color: "rgba(255,255,255,0.45)", marginBottom: 6, lineHeight: 1.3 }}>{comp.desc}</div>
                    <div style={{ height: 6, borderRadius: 3, background: "rgba(255,255,255,0.06)", overflow: "hidden" }}>
                      <div style={{ width: `${comp.val}%`, height: "100%", background: "linear-gradient(90deg, #3b82f6, #60a5fa)", borderRadius: 3, boxShadow: "0 0 8px rgba(59,130,246,0.4)" }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {!data && !error && !loading && (
        <div className="wc-card" style={{ color: "var(--color-accent)", background: "rgba(212,175,55,0.05)", border: "1px solid rgba(212,175,55,0.15)", borderRadius: 12, padding: "16px 20px", display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: "1.2rem" }}>ℹ️</span>
          <span>Select a national team from the selector above and click "Fetch metrics" to load the live analytics engine.</span>
        </div>
      )}
    </div>
  );
}

