/**
 * Rankings - live country intelligence view.
 */

import { useEffect, useState } from "react";
import { apiGet } from "@/services/api";
import { USE_MOCKS } from "@/dev/devFlags";
import { getMockCountryRankings } from "@/dev/mockResponses";
import type { CountryRankingRow } from "@/contracts";

const CONFEDERATIONS = ["All", "UEFA", "CONMEBOL", "CONCACAF", "CAF", "AFC", "OFC"];

export default function RankingsPage() {
  const [conf, setConf] = useState("All");
  const [limit, setLimit] = useState(16);
  const [data, setData] = useState<CountryRankingRow[]>([]);
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    const confParam = conf === "All" ? "" : conf;

    apiGet<{ data?: CountryRankingRow[] }>(`/api/v1/countries/rankings?confederation=${confParam}&limit=${limit}`).then((res) => {
      setLoading(false);

      if (res.error || !res.data) {
        if (USE_MOCKS) {
          setData(getMockCountryRankings().slice(0, limit));
          setNote("Using dev mock rankings.");
        } else {
          setData([]);
          setNote("No live rankings available.");
        }
        return;
      }

      const rows = Array.isArray(res.data) ? res.data : (res.data as { data?: CountryRankingRow[] }).data;
      if (rows && rows.length > 0) {
        setData(rows);
        setNote("");
      } else if (USE_MOCKS) {
        setData(getMockCountryRankings().slice(0, limit));
        setNote("Using dev mock rankings.");
      } else {
        setData([]);
        setNote("No live rankings available.");
      }
    });
  }, [conf, limit]);

  return (
    <div className="page-container">
      <div className="card" style={{ marginBottom: 16 }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 16, alignItems: "flex-start", flexWrap: "wrap" }}>
          <div>
            <div className="section-kicker">Country intelligence</div>
            <h1 style={{ fontSize: "1.7rem", marginBottom: 8 }}>World rankings</h1>
            <p style={{ color: "var(--color-text-secondary)", fontSize: "0.875rem", maxWidth: 760, lineHeight: 1.6 }}>
              Rank countries by live backend strength, attack, defense, and form. The top of the table is intentionally authoritative.
            </p>
          </div>
          <div className="badge badge-info">{USE_MOCKS ? "DEV MOCKS" : "LIVE RANKINGS"}</div>
        </div>

        <div style={{ display: "flex", gap: 12, alignItems: "end", flexWrap: "wrap", marginTop: 14 }}>
        <div>
          <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "var(--color-text-secondary)", marginBottom: 4 }}>
            Confederation
          </label>
          <select className="select" value={conf} onChange={(e) => setConf(e.target.value)}>
            {CONFEDERATIONS.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "var(--color-text-secondary)", marginBottom: 4 }}>
            Show top: {limit}
          </label>
          <input type="range" min={8} max={64} value={limit} onChange={(e) => setLimit(Number(e.target.value))} style={{ width: 160 }} />
        </div>
      </div>
      </div>

      <div className="layout-3col" style={{ marginBottom: 16 }}>
        {data.slice(0, 3).map((row, index) => (
          <div key={row.country_uid} className="card">
            <div className="section-kicker">Top {index + 1}</div>
            <div style={{ fontSize: "1.2rem", fontWeight: 800, marginBottom: 4 }}>{row.country_name}</div>
            <div style={{ color: "var(--color-text-secondary)", fontSize: "0.8125rem", marginBottom: 10 }}>
              {row.confederation ?? "Confederation not listed"}
            </div>
            <div style={{ display: "grid", gap: 8 }}>
              {[
                { label: "Elo", value: row.elo_rating, color: "var(--color-accent)" },
                { label: "Attack", value: row.attack_rating, color: "var(--color-green)" },
                { label: "Defense", value: row.defense_rating, color: "var(--color-gold)" },
              ].map((item) => (
                <div key={item.label}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                    <span style={{ fontSize: "0.75rem", color: "var(--color-text-secondary)" }}>{item.label}</span>
                    <span style={{ fontSize: "0.8rem", fontWeight: 700 }}>{item.value}</span>
                  </div>
                  <div className="prob-bar">
                    <div className="prob-bar-fill" style={{ width: `${Math.min(100, Number(item.value) / 20)}%`, background: item.color }} />
                  </div>
                </div>
              ))}
              <div style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", marginTop: 2 }}>
                Form: {row.recent_form_score ?? "-"} · Momentum: {row.momentum_score ?? "-"}
              </div>
            </div>
          </div>
        ))}
      </div>

      {note && (
        <div style={{ background: "rgba(88,166,255,0.08)", border: "1px solid rgba(88,166,255,0.2)", borderRadius: 6, padding: "8px 12px", fontSize: "0.8125rem", color: "var(--color-accent)", marginBottom: 12 }}>
          ℹ {note}
        </div>
      )}

      {loading && (
        <div style={{ padding: "16px 0", fontSize: "0.8125rem", color: "var(--color-text-secondary)" }}>
          <span className="spinner" style={{ marginRight: 8 }} /> Loading rankings...
        </div>
      )}

      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Country</th>
              <th className="text-right">Elo</th>
              <th className="text-right">Attack</th>
              <th className="text-right">Defense</th>
              <th className="text-right">Form</th>
            </tr>
          </thead>
          <tbody>
            {data.length > 0 ? (
              data.map((row) => (
                <tr key={row.country_uid} style={row.rank <= 3 ? { background: "rgba(88,166,255,0.05)" } : undefined}>
                  <td>{row.rank}</td>
                  <td style={{ fontWeight: 600 }}>{row.country_name}</td>
                  <td className="text-right text-mono">{row.elo_rating}</td>
                  <td className="text-right text-mono">{row.attack_rating}</td>
                  <td className="text-right text-mono">{row.defense_rating}</td>
                  <td className="text-right text-mono">{row.recent_form_score ?? "-"}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={6} style={{ color: "var(--color-text-muted)", padding: 16 }}>
                  No live ranking data available yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
