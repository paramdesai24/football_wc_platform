/**
 * Team Analytics — mirrors render_analytics_page() from Streamlit app.py
 *
 * Layout:
 *   - Team selector (selectbox)
 *   - Fetch Analytics button
 *   - JSON response display from /api/v1/analytics/team/{team_id}
 */

import { useState } from "react";
import { TEAMS, TEAM_NAMES, apiGet } from "@/services/api";

export default function TeamAnalyticsPage() {
  const [teamName, setTeamName] = useState(TEAM_NAMES[0] || "");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState("");

  const handleFetch = async () => {
    setLoading(true);
    setData(null);
    setError("");
    const teamId = TEAMS[teamName];
    const res = await apiGet<Record<string, unknown>>(`/api/v1/analytics/team/${teamId}`);
    setLoading(false);

    if (res.error) {
      setError(`Analytics unavailable: ${res.error}`);
    } else if (res.data) {
      setData(res.data);
    }
  };

  return (
    <div className="page-container">
      {/* Title — mirrors st.title("📈 Team Analytics") */}
      <h1 style={{ fontSize: "1.25rem", marginBottom: 16 }}>📈 Team Analytics</h1>

      {/* Team selector — mirrors st.selectbox("Select Team", TEAM_NAMES) */}
      <div style={{ display: "flex", gap: 12, alignItems: "end", marginBottom: 16 }}>
        <div>
          <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "var(--color-text-secondary)", marginBottom: 4 }}>
            Select Team
          </label>
          <select
            className="select"
            value={teamName}
            onChange={(e) => setTeamName(e.target.value)}
          >
            {TEAM_NAMES.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>

        <button className="btn btn-primary" disabled={loading} onClick={handleFetch}>
          {loading ? <><span className="spinner" /> Fetching...</> : "Fetch Analytics"}
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

      {/* JSON display — mirrors st.json(response) */}
      {data && (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <pre
            style={{
              padding: 14,
              fontSize: "0.75rem",
              color: "var(--color-text-secondary)",
              background: "var(--color-bg)",
              margin: 0,
              overflow: "auto",
              maxHeight: 600,
              lineHeight: 1.5,
            }}
          >
            {JSON.stringify(data, null, 2)}
          </pre>
        </div>
      )}

      {!data && !error && !loading && (
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
          ℹ Select a team and click Fetch Analytics to view data.
        </div>
      )}
    </div>
  );
}
