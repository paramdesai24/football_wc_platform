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
        { label: "Smart Score", value: Math.round(data.elo_rating), tone: "var(--color-accent)", fill: smartScoreBar(data.elo_rating) },
        { label: "Attack", value: Math.round(data.attack_rating), tone: "var(--color-green)", fill: ratingBar(data.attack_rating) },
        { label: "Defense", value: Math.round(data.defense_rating), tone: "var(--color-gold)", fill: ratingBar(data.defense_rating) },
      ]
    : [];

  return (
    <div className="page-container">
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
              {data ? `Rank ${data.rank ?? "-"} · ${data.confederation ?? "Unknown confederation"}` : "Load a team card to reveal the latest analytics bundle."}
            </div>
          </div>
        </div>
      </div>

      <div className="layout-hero-compact analytics-controls" style={{ marginBottom: 16 }}>
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
                {data.confederation ?? "-"} · Rank {data.rank ?? "-"}
              </div>
            </div>
            <div className="momentum-badge">
              Momentum <span>{Number(data.momentum).toFixed(2)}</span>
            </div>
          </div>

          <div className="layout-3col">
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
