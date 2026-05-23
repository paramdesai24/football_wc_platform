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

import { useState, useCallback } from "react";
import type { TournamentMatchResponse, TournamentStateResponse } from "@/contracts";
import {
  apiGet,
  apiPost,
  normalizeState,
  stageTitle,
  stageRank,
  scoreText,
  STAGE_ORDER,
} from "@/services/api";

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
    <div className="match-card" style={{ marginBottom: 8 }}>
      <div className="match-card-header">
        <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
          <span className={chipClass}>{stageTitle(stage)}</span>
          <span className="chip chip-status">{status}</span>
        </div>
        <span style={{ fontSize: "0.75rem", color: "var(--color-text-muted)" }}>
          M{match.match_id}
        </span>
      </div>
      <div className="teams">{match.home_team || "TBD"} vs {match.away_team || "TBD"}</div>
      <div className="score">{scoreText(match as Record<string, unknown>)}</div>
      <div className="meta">Winner: {match.winner || "TBD"}</div>
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

// ---- main ----
export default function TournamentPage() {
  const [state, setState] = useState<TournamentStateResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);

  const loadState = useCallback(async (refresh: boolean, simulations?: number) => {
    setLoading(true);
    let params = `?refresh=${refresh}`;
    if (simulations != null) params += `&simulations=${simulations}`;
    const res = await apiGet<TournamentStateResponse>(`/api/v1/tournament_results${params}`);
    setLoading(false);
    if (!res.error && res.data) {
      setState(normalizeState(res.data) as TournamentStateResponse);
    } else if (res.error) {
      setState(null);
    }
  }, []);

  const handleOverride = async (payload: Record<string, unknown>) => {
    const res = await apiPost<TournamentStateResponse>("/api/v1/override_match", payload);
    if (!res.error && res.data) {
      setState(normalizeState(res.data) as TournamentStateResponse);
      setEditingId(null);
    }
  };

  const matches = (state?.matches ?? []).slice().sort(
    (a, b) => stageRank(a.stage ?? "") - stageRank(b.stage ?? "") || (a.match_id ?? 0) - (b.match_id ?? 0)
  );

  const groupStandings = state?.group_standings ?? {};

  return (
    <div className="page-container">
      <div className="card" style={{ marginBottom: 16 }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 16, alignItems: "flex-start", flexWrap: "wrap" }}>
          <div>
            <div style={{ fontSize: "0.75rem", letterSpacing: 1.2, textTransform: "uppercase", color: "var(--color-text-muted)", marginBottom: 8 }}>
              Simulation center
            </div>
            <h1 style={{ fontSize: "1.7rem", marginBottom: 8 }}>Tournament simulation intelligence</h1>
            <p style={{ color: "var(--color-text-secondary)", fontSize: "0.875rem", maxWidth: 760, lineHeight: 1.6 }}>
              Run the full tournament model, edit non-final matches, and resimulate from the impacted stage onward.
            </p>
          </div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <button
              className="btn btn-primary"
              disabled={loading}
              onClick={() => loadState(true, 10)}
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
          ℹ No tournament state available yet.
        </div>
      )}

      {state && (
        <>
          <div className="layout-hero-compact" style={{ marginBottom: 16 }}>
            <div className="card">
              <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 10, marginBottom: 14 }}>
                <div>
                  <div style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", marginBottom: 4 }}>Champion</div>
                  <div style={{ fontSize: "1.25rem", fontWeight: 800 }}>{state.champion || "TBD"}</div>
                </div>
                <div>
                  <div style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", marginBottom: 4 }}>Runner-up</div>
                  <div style={{ fontSize: "1.25rem", fontWeight: 800 }}>{state.runner_up || "TBD"}</div>
                </div>
                <div>
                  <div style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", marginBottom: 4 }}>Third Place</div>
                  <div style={{ fontSize: "1.25rem", fontWeight: 800 }}>{state.third_place || "TBD"}</div>
                </div>
                <div>
                  <div style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", marginBottom: 4 }}>Matches</div>
                  <div style={{ fontSize: "1.25rem", fontWeight: 800 }}>{matches.length}</div>
                </div>
              </div>

              <div style={{ display: "grid", gap: 8 }}>
                <div style={{ fontSize: "0.75rem", color: "var(--color-text-muted)" }}>Tournament pulse</div>
                <div style={{ color: "var(--color-text-secondary)", lineHeight: 1.6 }}>
                  {matches.length > 0
                    ? `${matches.filter((m) => m.stage === "final").length > 0 ? "The final is staged and the bracket is ready for review." : "The bracket is progressing through the knockout path."}`
                    : "Run a simulation to generate the latest knockout projection and group-state outcomes."}
                </div>
              </div>
            </div>

            <div className="card">
              <div style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", marginBottom: 8 }}>Match control summary</div>
              <div style={{ display: "grid", gap: 10 }}>
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                    <span style={{ fontSize: "0.8rem", color: "var(--color-text-secondary)" }}>Editability</span>
                    <span style={{ fontSize: "0.8rem", fontWeight: 700 }}>{matches.some((m) => m.editable) ? "Available" : "Locked"}</span>
                  </div>
                  <div className="prob-bar"><div className="prob-bar-fill" style={{ width: matches.some((m) => m.editable) ? "78%" : "32%", background: "var(--color-accent)" }} /></div>
                </div>
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                    <span style={{ fontSize: "0.8rem", color: "var(--color-text-secondary)" }}>Bracket coverage</span>
                    <span style={{ fontSize: "0.8rem", fontWeight: 700 }}>{matches.length}</span>
                  </div>
                  <div className="prob-bar"><div className="prob-bar-fill" style={{ width: `${Math.min(100, matches.length * 5)}%`, background: "var(--color-green)" }} /></div>
                </div>
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                    <span style={{ fontSize: "0.8rem", color: "var(--color-text-secondary)" }}>Group tables</span>
                    <span style={{ fontSize: "0.8rem", fontWeight: 700 }}>{Object.keys(groupStandings).length}</span>
                  </div>
                  <div className="prob-bar"><div className="prob-bar-fill" style={{ width: `${Math.min(100, Object.keys(groupStandings).length * 10)}%`, background: "var(--color-gold)" }} /></div>
                </div>
              </div>
            </div>
          </div>

          {/* Group Stage Results — mirrors st.subheader("Group Stage Results") + expanders */}
          <h2 style={{ fontSize: "1rem", marginBottom: 10 }}>Group Stage Results</h2>
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
                          {Object.values(row || {}).map((val, j) => (
                            <td key={j}>{String(val ?? "")}</td>
                          ))}
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
                    gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
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
