/**
 * Play As A Team — mirrors render_play_as_page() from Streamlit app.py
 *
 * Layout:
 *   - Team selector
 *   - Number of simulations input
 *   - Run Play As Simulations button
 *   - Summary metrics (Titles Won, Avg Finish, Goals Scored, Goals Conceded, ET Freq, Pen Freq)
 *   - Elimination Distribution table
 *   - Simulation Journeys (expandable per simulation, with match details + timeline)
 */

import { useState, useEffect } from "react";
import type { PlayAsTeamResponse, TournamentStateResponse, TournamentMatchResponse } from "@/contracts";
import { apiGet, apiPost, normalizeState, stageTitle, TEAM_NAMES } from "@/services/api";

interface TimelineEvent {
  minute?: string;
  label?: string;
  event_type?: string;
  team?: string;
  note?: string;
}

interface Journey {
  simulation?: number;
  stage_reached?: string;
  momentum_summary?: string;
  matches?: Array<TournamentMatchResponse & {
    stage_label?: string;
    opponent?: string;
    is_home?: boolean;
    goals_for?: number;
    goals_against?: number;
    timeline?: TimelineEvent[];
  }>;
}

function Expander({
  title,
  defaultOpen = false,
  children,
}: {
  title: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="expander">
      <button className="expander-header" onClick={() => setOpen(!open)}>
        <span>{title}</span>
        <span style={{ fontSize: "0.75rem" }}>{open ? "▾" : "▸"}</span>
      </button>
      {open && <div className="expander-body">{children}</div>}
    </div>
  );
}

function resultBadge(stageReached: string): string {
  if (stageReached === "Champion") return "🏆 Champion";
  if (stageReached === "Runner-up") return "🥈 Runner-up";
  if (stageReached === "Third Place" || stageReached === "Fourth Place") return `🥉 ${stageReached}`;
  return `🎯 ${stageReached}`;
}

export default function PlayAsTeamPage() {
  const [availableTeams, setAvailableTeams] = useState<string[]>(TEAM_NAMES);
  const [selectedTeam, setSelectedTeam] = useState("Argentina");
  const [simulations, setSimulations] = useState(10);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PlayAsTeamResponse | null>(null);
  const [error, setError] = useState("");

  // Try to load available teams from tournament state
  useEffect(() => {
    apiGet<TournamentStateResponse>("/api/v1/tournament_results?refresh=false").then((res) => {
      if (!res.error && res.data) {
        const state = normalizeState(res.data);
        const matches = (state.matches as TournamentMatchResponse[]) ?? [];
        const teams = new Set<string>();
        matches.forEach((m) => {
          const home = String(m.home_team ?? "").trim();
          const away = String(m.away_team ?? "").trim();
          if (home) teams.add(home);
          if (away) teams.add(away);
        });
        if (teams.size > 0) {
          const sorted = [...teams].sort();
          setAvailableTeams(sorted);
          if (!sorted.includes(selectedTeam) && sorted.length > 0) {
            setSelectedTeam(sorted.includes("Argentina") ? "Argentina" : (sorted[0] || ""));
          }
        }
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSimulate = async () => {
    setLoading(true);
    setResult(null);
    setError("");
    const res = await apiPost<PlayAsTeamResponse>( 
      "/api/v1/play_as",
      { team_name: selectedTeam, simulations },
      240000
    );
    setLoading(false);

    if (res.error) {
      setError(`Play As simulation failed: ${res.error}`);
    } else if (res.data) {
      setResult(normalizeState(res.data) as PlayAsTeamResponse);
    }
  };

  const summary = result?.summary ?? {};
  const journeys = result?.journeys ?? [];

  return (
    <div className="page-container">
      <div className="card" style={{ marginBottom: 16 }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 16, alignItems: "flex-start", flexWrap: "wrap" }}>
          <div>
            <div style={{ fontSize: "0.75rem", letterSpacing: 1.2, textTransform: "uppercase", color: "var(--color-text-muted)", marginBottom: 8 }}>
              Simulation journeys
            </div>
            <h1 style={{ fontSize: "1.7rem", marginBottom: 8 }}>Play as a team</h1>
            <p style={{ color: "var(--color-text-secondary)", fontSize: "0.875rem", maxWidth: 760, lineHeight: 1.6 }}>
              Simulate multiple tournaments for one team and inspect the paths they take through the competition.
            </p>
          </div>
          <div className="badge badge-info">{loading ? "SIMULATING" : "READY"}</div>
        </div>
      </div>

      {/* Controls — mirrors controls = st.columns([2, 1, 1, 2]) */}
      <div className="card" style={{ display: "flex", gap: 12, alignItems: "end", flexWrap: "wrap", marginBottom: 16 }}>
        <div>
          <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "var(--color-text-secondary)", marginBottom: 4 }}>
            Select Team
          </label>
          <select
            className="select"
            value={selectedTeam}
            onChange={(e) => setSelectedTeam(e.target.value)}
          >
            {availableTeams.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>

        <div>
          <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "var(--color-text-secondary)", marginBottom: 4 }}>
            Simulations
          </label>
          <input
            type="number"
            className="input-field"
            min={1}
            max={25}
            value={simulations}
            onChange={(e) => setSimulations(Number(e.target.value))}
            style={{ width: 80 }}
          />
        </div>

        <button className="btn btn-primary" disabled={loading} onClick={handleSimulate}>
          {loading ? <><span className="spinner" /> Simulating...</> : "Run Play As Simulations"}
        </button>
      </div>

      {error && (
        <div
          style={{
            background: "rgba(248,81,73,0.08)",
            border: "1px solid rgba(248,81,73,0.2)",
            borderRadius: 6,
            padding: "8px 12px",
            fontSize: "0.8125rem",
            color: "var(--color-red)",
            marginBottom: 12,
          }}
        >
          {error}
        </div>
      )}

      {!result && !loading && !error && (
        <div
          style={{
            background: "rgba(88,166,255,0.08)",
            border: "1px solid rgba(88,166,255,0.2)",
            borderRadius: 6,
            padding: "8px 12px",
            fontSize: "0.8125rem",
            color: "var(--color-accent)",
          }}
        >
          ℹ Choose a team and run simulations to see tournament journeys.
        </div>
      )}

      {result && (
        <>
          <div className="layout-hero-compact" style={{ marginBottom: 16 }}>
            <div className="card">
              <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 10, marginBottom: 14 }}>
                <div><div style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", marginBottom: 4 }}>Titles Won</div><div style={{ fontSize: "1.25rem", fontWeight: 800 }}>{summary.titles_won ?? 0}</div></div>
                <div><div style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", marginBottom: 4 }}>Average Finish</div><div style={{ fontSize: "1.25rem", fontWeight: 800 }}>{summary.average_finish ?? "N/A"}</div></div>
                <div><div style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", marginBottom: 4 }}>Goals Scored</div><div style={{ fontSize: "1.25rem", fontWeight: 800 }}>{summary.goals_scored ?? summary.average_goals_for ?? 0}</div></div>
                <div><div style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", marginBottom: 4 }}>Goals Conceded</div><div style={{ fontSize: "1.25rem", fontWeight: 800 }}>{summary.goals_conceded ?? summary.average_goals_against ?? 0}</div></div>
              </div>

              <div style={{ display: "grid", gap: 10 }}>
                {[
                  { label: "ET frequency", value: (summary.et_frequency ?? 0) * 100, color: "var(--color-yellow)" },
                  { label: "Penalty frequency", value: (summary.penalty_frequency ?? 0) * 100, color: "var(--color-accent)" },
                ].map((item) => (
                  <div key={item.label}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                      <span style={{ fontSize: "0.8rem", color: "var(--color-text-secondary)" }}>{item.label}</span>
                      <span style={{ fontSize: "0.8rem", fontWeight: 700 }}>{item.value.toFixed(1)}%</span>
                    </div>
                    <div className="prob-bar">
                      <div className="prob-bar-fill" style={{ width: `${Math.min(100, item.value)}%`, background: item.color }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="card">
              <div style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", marginBottom: 8 }}>Elimination distribution</div>
              {summary.elimination_distribution && Object.keys(summary.elimination_distribution).length > 0 ? (
                <div style={{ display: "grid", gap: 8 }}>
                  {Object.entries(summary.elimination_distribution)
                    .sort(([, a], [, b]) => b - a)
                    .map(([stage, count]) => (
                      <div key={stage}>
                        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                          <span style={{ fontSize: "0.8rem", color: "var(--color-text-secondary)" }}>{stage}</span>
                          <span style={{ fontSize: "0.8rem", fontWeight: 700 }}>{count}</span>
                        </div>
                        <div className="prob-bar">
                          <div className="prob-bar-fill" style={{ width: `${Math.min(100, count * 8)}%`, background: "var(--color-green)" }} />
                        </div>
                      </div>
                    ))}
                </div>
              ) : (
                <p style={{ fontSize: "0.75rem", color: "var(--color-text-muted)" }}>No elimination data available.</p>
              )}
            </div>
          </div>

          {/* Simulation Journeys — mirrors st.subheader("Simulation Journeys") */}
          <div className="section-heading">
            <div>
              <h2 style={{ fontSize: "1rem", marginBottom: 4 }}>Simulation Journeys</h2>
              <div style={{ color: "var(--color-text-muted)", fontSize: "0.8125rem" }}>How one team's path changes across repeated tournament runs.</div>
            </div>
            <div className="badge badge-info">{journeys.length} journeys</div>
          </div>
          {journeys.map((journey) => {
            const simNo = journey.simulation;
            const stageReached = journey.stage_reached || "Unknown";
            const title = `Simulation ${simNo}: ${resultBadge(stageReached)}`;

            return (
              <Expander key={simNo} title={title} defaultOpen={simNo === 1}>
                {journey.momentum_summary && (
                  <div
                    style={{
                      background: "rgba(88,166,255,0.08)",
                      border: "1px solid rgba(88,166,255,0.2)",
                      borderRadius: 6,
                      padding: "8px 12px",
                      fontSize: "0.8125rem",
                      color: "var(--color-accent)",
                      marginBottom: 8,
                    }}
                  >
                    {journey.momentum_summary}
                  </div>
                )}

                {(journey.matches ?? []).map((match, mi) => {
                  const stageLabel = match.stage_label || stageTitle(match.stage || "");
                  const etPen: string[] = [];
                  if (match.extra_time) etPen.push("AET");
                  if (match.penalties) etPen.push(`Pens ${match.penalty_score || ""}`);

                  // Build scoreline
                  const teamIsHome = !!match.is_home;
                  const opponent = match.opponent || "TBD";
                  const scoreline = teamIsHome
                    ? `${selectedTeam} ${match.goals_for}-${match.goals_against} ${opponent}`
                    : `${opponent} ${match.goals_against}-${match.goals_for} ${selectedTeam}`;

                  return (
                    <div key={mi} style={{ marginBottom: 10 }}>
                      <div style={{ fontWeight: 700, fontSize: "0.8125rem" }}>{stageLabel}</div>
                      <div style={{ fontSize: "0.8125rem" }}>{scoreline}</div>
                      {etPen.length > 0 && (
                        <div style={{ fontSize: "0.75rem", color: "var(--color-text-muted)" }}>
                          {etPen.join(" | ")}
                        </div>
                      )}

                      {/* Timeline events */}
                      {match.timeline && match.timeline.length > 0 && (
                        <div style={{ marginTop: 4 }}>
                          {match.timeline.map((evt, ei) => (
                            <div
                              key={ei}
                              style={{
                                display: "grid",
                                gridTemplateColumns: "50px 1fr",
                                gap: 4,
                                fontSize: "0.75rem",
                                padding: "2px 0",
                                borderBottom: "1px solid var(--color-border-subtle)",
                              }}
                            >
                              <span style={{ fontWeight: 700, color: "var(--color-text-secondary)" }}>
                                {evt.minute}
                              </span>
                              <div>
                                <span style={{ fontWeight: 600 }}>
                                  {evt.label || evt.event_type || "Event"}
                                  {evt.team && evt.team !== "Match" ? ` - ${evt.team}` : ""}
                                </span>
                                {evt.note && (
                                  <div style={{ color: "var(--color-text-muted)", fontSize: "0.6875rem" }}>
                                    {evt.note}
                                  </div>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </Expander>
            );
          })}
        </>
      )}

      {!result && !loading && !error && (
        <div className="loading-panel" style={{ marginTop: 16 }}>
          <div className="loading-line long" style={{ marginBottom: 8 }} />
          <div className="loading-line medium" style={{ marginBottom: 8 }} />
          <div className="loading-line short" />
        </div>
      )}
    </div>
  );
}
