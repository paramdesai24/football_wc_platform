/**
 * Predictions — mirrors render_predictions_page() from Streamlit app.py
 *
 * Layout:
 *   - Home / Away team selectors (side by side)
 *   - Generate Prediction button
 *   - Result: 4 metrics (Home Win, Draw, Away Win, Confidence)
 *   - Predicted score + explanation
 *   - Divider
 *   - Prediction History table (last 5)
 */

import { useState, useEffect } from "react";
import { TEAMS, TEAM_NAMES, apiGet, apiPost } from "@/services/api";
import type { PredictionHistoryRow, PredictionResponse } from "@/contracts";

export default function PredictionsPage() {
  const [homeTeam, setHomeTeam] = useState(TEAM_NAMES[0] || "");
  const [awayTeam, setAwayTeam] = useState(TEAM_NAMES[3] || "");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [history, setHistory] = useState<PredictionHistoryRow[]>([]);
  const [historyNote, setHistoryNote] = useState("");

  const fetchHistory = () => {
    apiGet<{ data?: PredictionHistoryRow[] }>("/api/v1/predictions/history?limit=5").then((res) => {
      if (res.error || !res.data) {
        setHistoryNote("No prediction history yet.");
      } else {
        const rows = Array.isArray(res.data) ? res.data : (res.data as { data?: PredictionHistoryRow[] }).data;
        if (rows && rows.length > 0) {
          setHistory(rows);
          setHistoryNote("");
        } else {
          setHistoryNote("No prediction history yet.");
        }
      }
    });
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handlePredict = async () => {
    setLoading(true);
    setResult(null);
    const payload = {
      home_team_id: TEAMS[homeTeam],
      away_team_id: TEAMS[awayTeam],
    };
    const res = await apiPost<PredictionResponse>("/api/v1/predictions/predict", payload);
    setLoading(false);

    if (res.error) {
      setResult({ error: `Prediction failed: ${res.error}` });
    } else if (res.data) {
      setResult(res.data);
      fetchHistory(); // refresh history
    }
  };

  return (
    <div className="page-container">
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="layout-hero-compact">
          <div>
            <div className="section-kicker">Match intelligence coverage</div>
            <h1 style={{ fontSize: "1.7rem", marginBottom: 8 }}>Match predictions</h1>
            <p style={{ color: "var(--color-text-secondary)", fontSize: "0.875rem", lineHeight: 1.6, maxWidth: 760 }}>
              Compare two teams, generate a backend prediction, and review the latest prediction history alongside the reasoning.
            </p>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 12, marginTop: 14 }}>
              <div>
                <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "var(--color-text-secondary)", marginBottom: 4 }}>
                  Home Team
                </label>
                <select className="select" style={{ width: "100%" }} value={homeTeam} onChange={(e) => setHomeTeam(e.target.value)}>
                  {TEAM_NAMES.map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>
              <div>
                <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "var(--color-text-secondary)", marginBottom: 4 }}>
                  Away Team
                </label>
                <select className="select" style={{ width: "100%" }} value={awayTeam} onChange={(e) => setAwayTeam(e.target.value)}>
                  {TEAM_NAMES.map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>
            </div>

            <button className="btn btn-primary" disabled={loading} onClick={handlePredict} style={{ marginTop: 14 }}>
              {loading ? <><span className="spinner" /> Predicting...</> : "Generate Prediction"}
            </button>
          </div>

          <div className="card" style={{ background: "var(--color-bg-raised)" }}>
            <div className="section-kicker">Prediction summary</div>
            {result && !result.error ? (
              <div style={{ display: "grid", gap: 10 }}>
                <div>
                  <div style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", marginBottom: 4 }}>Predicted score</div>
                  <div style={{ fontSize: "1.45rem", fontWeight: 800 }}>{result.predicted_score ?? "TBD"}</div>
                </div>
                {[
                  { label: "Home win", value: result.home_win_pct ?? 0, color: "var(--color-green)" },
                  { label: "Draw", value: result.draw_pct ?? 0, color: "var(--color-yellow)" },
                  { label: "Away win", value: result.away_win_pct ?? 0, color: "var(--color-accent)" },
                  { label: "Confidence", value: result.confidence ?? 0, color: "var(--color-gold)" },
                ].map((item) => (
                  <div key={item.label}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                      <span style={{ fontSize: "0.8rem", color: "var(--color-text-secondary)" }}>{item.label}</span>
                      <span style={{ fontSize: "0.8rem", fontWeight: 700 }}>{item.value}%</span>
                    </div>
                    <div className="prob-bar">
                      <div className="prob-bar-fill" style={{ width: `${Math.min(100, item.value)}%`, background: item.color }} />
                    </div>
                  </div>
                ))}
                <div style={{ color: "var(--color-text-secondary)", fontSize: "0.78rem", lineHeight: 1.6, marginTop: 4 }}>
                  {result.home_xg != null || result.away_xg != null
                    ? `xG: ${result.home_xg ?? 0} to ${result.away_xg ?? 0}`
                    : "xG data will appear when the backend model exposes it."}
                </div>
              </div>
            ) : (
              <div style={{ color: "var(--color-text-secondary)", fontSize: "0.85rem", lineHeight: 1.6 }}>
                Run a prediction to compare win probabilities, confidence, and the backend-generated scoreline.
              </div>
            )}
          </div>
        </div>
      </div>

      {result && !result.error && (
        <div className="card" style={{ marginBottom: 16 }}>
          <div className="section-heading">
            <div>
              <h2 style={{ fontSize: "1rem", marginBottom: 4 }}>Probability breakdown</h2>
              <div style={{ color: "var(--color-text-muted)", fontSize: "0.8125rem" }}>Match intelligence and reasoning from the prediction engine</div>
            </div>
            <div className="badge badge-success">Live prediction</div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 10, marginBottom: 14 }}>
            {[
              { label: "Home Win", value: result.home_win_pct ?? 0, color: "var(--color-green)" },
              { label: "Draw", value: result.draw_pct ?? 0, color: "var(--color-yellow)" },
              { label: "Away Win", value: result.away_win_pct ?? 0, color: "var(--color-accent)" },
              { label: "Confidence", value: result.confidence ?? 0, color: "var(--color-gold)" },
            ].map((item) => (
              <div key={item.label} className="card-compact">
                <div className="metric">
                  <span className="metric-label">{item.label}</span>
                  <span className="metric-value" style={{ fontSize: "1rem" }}>{item.value}%</span>
                </div>
                <div className="prob-bar" style={{ marginTop: 8 }}>
                  <div className="prob-bar-fill" style={{ width: `${Math.min(100, item.value)}%`, background: item.color }} />
                </div>
              </div>
            ))}
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 1fr) minmax(280px, 0.72fr)", gap: 16 }}>
            <div>
              <div style={{ background: "rgba(63,185,80,0.08)", border: "1px solid rgba(63,185,80,0.2)", borderRadius: 6, padding: "10px 12px", fontSize: "0.875rem", fontWeight: 600, color: "var(--color-green)", marginBottom: result.explanation ? 8 : 0 }}>
                {result.match ? `✓ Prediction: ${result.match}` : "Prediction generated"} → {result.predicted_score ?? "TBD"}
              </div>

              {result.explanation && (
                <div style={{ color: "var(--color-text-secondary)", fontSize: "0.85rem", lineHeight: 1.65 }}>
                  {result.explanation}
                </div>
              )}
            </div>

            <div className="card" style={{ background: "var(--color-bg-raised)" }}>
              <div style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", marginBottom: 8 }}>Coverage notes</div>
              <div style={{ display: "grid", gap: 10 }}>
                <div>
                  <div style={{ fontSize: "0.8rem", color: "var(--color-text-secondary)", marginBottom: 4 }}>Home team</div>
                  <div style={{ fontWeight: 700 }}>{result.home_team ?? homeTeam}</div>
                </div>
                <div>
                  <div style={{ fontSize: "0.8rem", color: "var(--color-text-secondary)", marginBottom: 4 }}>Away team</div>
                  <div style={{ fontWeight: 700 }}>{result.away_team ?? awayTeam}</div>
                </div>
                <div>
                  <div style={{ fontSize: "0.8rem", color: "var(--color-text-secondary)", marginBottom: 4 }}>xG</div>
                  <div style={{ fontWeight: 700 }}>{result.home_xg ?? 0} - {result.away_xg ?? 0}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {result?.error && (
        <div
          style={{
            background: "rgba(248,81,73,0.08)",
            border: "1px solid rgba(248,81,73,0.2)",
            borderRadius: 6,
            padding: "8px 12px",
            fontSize: "0.8125rem",
            color: "var(--color-red)",
            marginBottom: 16,
          }}
        >
          {result.error}
        </div>
      )}

      <hr className="divider" />

      {/* Prediction History — mirrors st.subheader("Prediction History") + render_prediction_history() */}
      <div className="section-heading">
        <div>
          <h2 style={{ fontSize: "1rem", marginBottom: 4 }}>Prediction History</h2>
          <div style={{ color: "var(--color-text-muted)", fontSize: "0.8125rem" }}>Recent match outcomes and confidence levels</div>
        </div>
      </div>
      {historyNote ? (
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
          ℹ {historyNote}
        </div>
      ) : (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Match</th>
                <th>Prediction</th>
                <th className="text-center">Confidence</th>
                <th className="text-center">Win %</th>
                <th className="text-center">Draw %</th>
                <th className="text-center">Loss %</th>
              </tr>
            </thead>
            <tbody>
              {history.map((h, i) => (
                <tr key={i}>
                  <td style={{ fontSize: "0.75rem", color: "var(--color-text-muted)" }}>{h.timestamp}</td>
                  <td style={{ fontWeight: 600 }}>{h.match}</td>
                  <td>{h.predicted_score}</td>
                  <td className="text-center">{h.confidence}</td>
                  <td className="text-center">{h.home_win_pct}</td>
                  <td className="text-center">{h.draw_pct}</td>
                  <td className="text-center">{h.away_win_pct}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
