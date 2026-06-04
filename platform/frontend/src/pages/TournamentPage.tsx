/**
 * Tournament Simulation — mirrors render_tournament_page() from Streamlit app.py
 *
 * Layout:
 *   - Run / Refresh buttons
 *   - Summary metrics (Champion, Runner-up, Third Place, Matches)
 *   - Group Stage Results (expandable per group, with standings tables)
 *   - Bracket (expandable per KO stage, with match cards)
 *   - Match editing (score override + resimulate)
 */

import { useCallback, useState } from "react";
import { useEffect } from "react";
import type { TournamentMatchResponse, TournamentStateResponse } from "@/contracts";
import {
  apiGet,
  apiPost,
  stageTitle,
  stageRank,
  scoreText,
  STAGE_ORDER,
} from "@/services/api";
import { FlagImg } from "@/components/FlagImg";
import { teamFlagCode } from "@/lib/flags";

// ---- helpers ----
function MatchCard({
  match,
  onEdit,
  editingId,
  onSaveOverride,
  onCancelEdit,
}: {
  match: TournamentMatchResponse;
  onEdit: (id: number) => void;
  editingId: number | null;
  onSaveOverride: (payload: Record<string, unknown>) => void;
  onCancelEdit: () => void;
}) {
  const stage = match.stage || "";
  const locked = !!match.locked;
  const editable = !!match.editable;
  const status = locked ? "Locked" : editable ? "Editable" : "Fixed";

  const chipClass = `chip chip-${stage.toLowerCase().replace("_", "")}`;
  const isEditing = editingId === match.match_id;

  const extraBits: string[] = [];
  if (match.user_overridden) extraBits.push("User override");
  if (match.extra_time) extraBits.push("AET");
  if (match.penalties) extraBits.push(`Pens ${match.penalty_score || ""}`);

  return (
    <div className="match-card wc-card" style={{ marginBottom: 8, padding: 16, display: "grid", gap: 12 }}>
      <div className="match-card-header">
        <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
          <span className={chipClass}>{stageTitle(stage)}</span>
          <span className="chip chip-status">{status}</span>
        </div>
        <span style={{ fontSize: "0.75rem", color: "var(--color-text-muted)" }}>
          M{match.match_id}
        </span>
      </div>
      <div className="teams" style={{ display: "grid", gap: 10 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, minWidth: 0 }}>
            <FlagImg code={teamFlagCode(match.home_team || "TBD")} size={28} />
            <span style={{ fontWeight: 700, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{match.home_team || "TBD"}</span>
          </div>
          <span className="wc-pill wc-pill-blue">Home</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, minWidth: 0 }}>
            <FlagImg code={teamFlagCode(match.away_team || "TBD")} size={28} />
            <span style={{ fontWeight: 700, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{match.away_team || "TBD"}</span>
          </div>
          <span className="wc-pill wc-pill-gold">Away</span>
        </div>
      </div>
      <div className="score">{scoreText(match as Record<string, unknown>)}</div>
      <div className="meta" style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span>Winner:</span>
        <FlagImg code={teamFlagCode(match.winner || "TBD")} size={18} />
        <span>{match.winner || "TBD"}</span>
      </div>
      {extraBits.length > 0 && (
        <div className="meta" style={{ color: "var(--color-text-muted)" }}>
          {extraBits.join(" · ")}
        </div>
      )}

      {/* Edit button */}
      {editable && stage !== "FINAL" && !isEditing && (
        <button
          className="btn"
          style={{ marginTop: 8, fontSize: "0.75rem", padding: "4px 10px" }}
          onClick={() => onEdit(match.match_id!)}
        >
          Edit
        </button>
      )}

      {/* Match editor */}
      {isEditing && (
        <MatchEditor
          match={match}
          onSave={onSaveOverride}
          onCancel={onCancelEdit}
        />
      )}
    </div>
  );
}

function MatchEditor({
  match,
  onSave,
  onCancel,
}: {
  match: TournamentMatchResponse;
  onSave: (payload: Record<string, unknown>) => void;
  onCancel: () => void;
}) {
  const [homeScore, setHomeScore] = useState(match.home_score ?? 0);
  const [awayScore, setAwayScore] = useState(match.away_score ?? 0);
  const [penWinner, setPenWinner] = useState<string>("home");
  const stage = match.stage || "";
  const showPens = stage !== "GROUP" && homeScore === awayScore;

  return (
    <div style={{ marginTop: 10, padding: 10, borderRadius: 6, border: "1px solid var(--color-border)", background: "var(--color-bg)" }}>
      <h4 style={{ fontSize: "0.8125rem", marginBottom: 8 }}>Edit Match Override</h4>
      <p style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", marginBottom: 8 }}>
        Match M{match.match_id} · {stageTitle(stage)}
      </p>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 8 }}>
        <div>
          <label style={{ display: "block", fontSize: "0.6875rem", color: "var(--color-text-secondary)", marginBottom: 2 }}>
            {match.home_team} score
          </label>
          <input
            type="number"
            className="input-field"
            style={{ width: "100%" }}
            min={0}
            value={homeScore}
            onChange={(e) => setHomeScore(Number(e.target.value))}
          />
        </div>
        <div>
          <label style={{ display: "block", fontSize: "0.6875rem", color: "var(--color-text-secondary)", marginBottom: 2 }}>
            {match.away_team} score
          </label>
          <input
            type="number"
            className="input-field"
            style={{ width: "100%" }}
            min={0}
            value={awayScore}
            onChange={(e) => setAwayScore(Number(e.target.value))}
          />
        </div>
      </div>

      {showPens && (
        <div style={{ marginBottom: 8 }}>
          <label style={{ display: "block", fontSize: "0.6875rem", color: "var(--color-text-secondary)", marginBottom: 2 }}>
            Penalty winner
          </label>
          <select className="select" value={penWinner} onChange={(e) => setPenWinner(e.target.value)}>
            <option value="home">{match.home_team}</option>
            <option value="away">{match.away_team}</option>
          </select>
        </div>
      )}

      <div style={{ display: "flex", gap: 8 }}>
        <button
          className="btn btn-primary"
          style={{ fontSize: "0.75rem", padding: "5px 10px" }}
          onClick={() => {
            const payload: Record<string, unknown> = {
              match_id: match.match_id,
              home_score: homeScore,
              away_score: awayScore,
            };
            if (showPens) payload.penalties_winner = penWinner;
            onSave(payload);
          }}
        >
          Save override
        </button>
        <button
          className="btn"
          style={{ fontSize: "0.75rem", padding: "5px 10px" }}
          onClick={onCancel}
        >
          Cancel
        </button>
      </div>
    </div>
  );
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

const TEAM_FLAG: Record<string, string> = {
  'Spain': 'es', 'France': 'fr', 'Germany': 'de', 'Brazil': 'br',
  'Argentina': 'ar', 'Portugal': 'pt', 'Netherlands': 'nl',
  'England': 'gb-eng', 'Italy': 'it', 'Japan': 'jp',
  'Morocco': 'ma', 'USA': 'us', 'Mexico': 'mx', 'Croatia': 'hr',
}
const getFlagCode = (name?: string) => {
  if (!name) return null;
  return TEAM_FLAG[name] ?? teamFlagCode(name) ?? null;
}

// ---- main ----
export default function TournamentPage() {
  const [state, setState] = useState<TournamentStateResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);

  const QUICK_TOURNAMENT_SIMULATIONS = 2;

  useEffect(() => {
    loadState(true, QUICK_TOURNAMENT_SIMULATIONS);
  }, []);

  const loadState = useCallback(async (refresh: boolean, simulations?: number) => {
    setLoading(true);
    let params = `?refresh=${refresh}`;
    if (simulations != null) params += `&simulations=${simulations}`;
    const res = await apiGet<TournamentStateResponse>(`/api/v1/tournament_results${params}`);
    setLoading(false);
    if (!res.error && res.data) {
      const payload = (res.data as { data?: TournamentStateResponse }).data ?? (res.data as TournamentStateResponse);
      console.log("Tournament response:", payload);
      setState(payload);
    } else if (res.error) {
      setState(null);
    }
  }, []);

  const handleOverride = async (payload: Record<string, unknown>) => {
    const res = await apiPost<TournamentStateResponse>("/api/v1/override_match", payload);
    if (!res.error && res.data) {
      const payloadData = (res.data as { data?: TournamentStateResponse }).data ?? (res.data as TournamentStateResponse);
      console.log("Tournament override response:", payloadData);
      setState(payloadData);
      setEditingId(null);
    }
  };

  const matches = (state?.matches ?? []).slice().sort(
    (a, b) => stageRank(a.stage ?? "") - stageRank(b.stage ?? "") || (a.match_id ?? 0) - (b.match_id ?? 0)
  );

  const groupStandings = state?.group_standings ?? {};

  return (
    <div className="page-container">
      <div className="wc-card section-card" style={{ marginBottom: 18 }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 16, alignItems: "flex-start", flexWrap: "wrap" }}>
          <div style={{ display: "grid", gap: 10 }}>
            <div className="eyebrow">Simulation center</div>
            <h1 className="page-title" style={{ fontSize: "1.75rem", marginBottom: 0 }}>Tournament simulation intelligence</h1>
            <p className="page-sub" style={{ maxWidth: 760 }}>
              Run the full tournament model, edit non-final matches, and resimulate from the impacted stage onward.
            </p>
          </div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <button
              className="btn btn-primary"
              disabled={loading}
              onClick={() => loadState(true, QUICK_TOURNAMENT_SIMULATIONS)}
            >
              {loading ? <><span className="spinner" /> Simulating...</> : "Run Tournament Simulation"}
            </button>
            <button className="btn" disabled={loading} onClick={() => loadState(false)}>
              Refresh Saved State
            </button>
          </div>
        </div>
      </div>

      {!state && !loading && (
        <div className="card-compact" style={{ color: "var(--color-accent)" }}>
          ℹ No tournament state available yet.
        </div>
      )}

      {state && (
        <>
          <div className="layout-hero-compact" style={{ marginBottom: 16 }}>
            <div className="wc-card section-card" style={{ display: "grid", gap: 14 }}>
              <div className="podium-grid">
                {[
                  { label: 'CHAMPION',   emoji: '🏆', value: state?.champion,    color: '#d4af37' },
                  { label: 'RUNNER-UP',  emoji: '🥈', value: state?.runner_up,   color: 'rgba(192,192,192,0.9)' },
                  { label: 'THIRD PLACE', emoji: '🥉', value: state?.third_place, color: 'rgba(205,127,50,0.9)' },
                ].map(item => {
                  const flagCode = getFlagCode(item.value)
                  return (
                    <div key={item.label} className="wc-card podium-card" style={{ background: "var(--color-bg-raised)", display: "flex", flexDirection: "column", alignItems: "center", gap: 6, padding: "12px 10px", border: `1px solid ${item.color}` }}>
                      <span style={{ fontSize: 24 }}>{item.emoji}</span>
                      <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.05em", color: "var(--color-text-muted)" }}>
                        {item.label}
                      </div>
                      {item.value ? (
                        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                          {flagCode && (
                            <FlagImg code={flagCode} size={16} />
                          )}
                          <span style={{ fontSize: "1.1rem", fontWeight: 700, color: "#fff", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                            {item.value}
                          </span>
                        </div>
                      ) : (
                        <span style={{ fontSize: "1.1rem", fontWeight: 700, color: "rgba(255,255,255,0.3)" }}>
                          TBD
                        </span>
                      )}
                    </div>
                  )
                })}
              </div>

              {/* Matches summary and tournament pulse removed — streamlined UI */}
            </div>

            <div className="wc-card" style={{ display: "grid", gap: 10, padding: 20 }}>
              <div style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", marginBottom: 8 }}>Match control summary</div>
              <div style={{ display: "grid", gap: 0 }}>
                <div className="control-row">
                  <div className="control-row-header">
                    <span className="control-label">Editability</span>
                    <span className="control-value">{matches.some((m) => m.editable) ? "Available" : "Locked"}</span>
                  </div>
                  <div className="control-bar-track"><div className="control-bar-fill" style={{ width: matches.some((m) => m.editable) ? "78%" : "32%" }} /></div>
                </div>
                <div className="control-row">
                  <div className="control-row-header">
                    <span className="control-label">Bracket coverage</span>
                    <span className="control-value">{matches.length}</span>
                  </div>
                  <div className="control-bar-track"><div className="control-bar-fill" style={{ width: `${Math.min(100, matches.length * 5)}%` }} /></div>
                </div>
                <div className="control-row" style={{ borderBottom: "none" }}>
                  <div className="control-row-header">
                    <span className="control-label">Group tables</span>
                    <span className="control-value">{Object.keys(groupStandings).length}</span>
                  </div>
                  <div className="control-bar-track"><div className="control-bar-fill" style={{ width: `${Math.min(100, Object.keys(groupStandings).length * 10)}%` }} /></div>
                </div>
              </div>
            </div>
          </div>

          {/* Group Stage Results — mirrors st.subheader("Group Stage Results") + expanders */}
          <div className="section-heading">
            <div>
              <h2 style={{ fontSize: "1rem", marginBottom: 4 }}>Group Stage Results</h2>
              <div style={{ color: "var(--color-text-muted)", fontSize: "0.8125rem" }}>Group tables and qualification flow</div>
            </div>
          </div>
          {Object.keys(groupStandings)
            .sort()
            .map((groupName) => {
              const rows = groupStandings[groupName] || [];
              return (
              <Expander key={groupName} title={`Group ${groupName}`}>
                <div className="table-wrap">
                  <table className="data-table">
                    <thead>
                      <tr>
                        {rows.length > 0 &&
                          Object.keys(rows[0] || {}).map((col) => (
                            <th key={col}>{col}</th>
                          ))}
                      </tr>
                    </thead>
                    <tbody>
                      {rows.map((row, i) => (
                        <tr key={i}>
                          {Object.entries(row || {}).map(([key, val], j) => {
                            const text = String(val ?? "");
                            if (key.toLowerCase().includes("team") || key.toLowerCase().includes("country")) {
                              return <td key={j} style={{ display: "flex", alignItems: "center", gap: 8 }}><FlagImg code={teamFlagCode(text)} size={16} /><span>{text}</span></td>;
                            }
                            return <td key={j}>{text}</td>;
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Expander>
            )})}

          {/* Bracket — mirrors st.subheader("Bracket") + stage expanders */}
          <h2 style={{ fontSize: "1rem", marginTop: 16, marginBottom: 10 }}>Bracket</h2>
          {STAGE_ORDER.filter((s) => s !== "GROUP").map((stage) => {
            const stageMatches = matches.filter((m) => m.stage === stage);
            if (stageMatches.length === 0) return null;
            return (
              <Expander
                key={stage}
                title={stageTitle(stage)}
                defaultOpen={stage === "SF" || stage === "FINAL"}
              >
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fill, minmax(290px, 1fr))",
                    gap: 8,
                  }}
                >
                  {stageMatches.map((m) => (
                    <MatchCard
                      key={m.match_id}
                      match={m}
                      onEdit={setEditingId}
                      editingId={editingId}
                      onSaveOverride={handleOverride}
                      onCancelEdit={() => setEditingId(null)}
                    />
                  ))}
                </div>
              </Expander>
            );
          })}
        </>
      )}

      {loading && !state && (
        <div className="loading-panel">
          <div className="metric" style={{ gap: 8 }}>
            <div className="spinner" />
            <div style={{ color: "var(--color-text-secondary)" }}>Loading tournament state and bracket intelligence...</div>
          </div>
        </div>
      )}
    </div>
  );
}
