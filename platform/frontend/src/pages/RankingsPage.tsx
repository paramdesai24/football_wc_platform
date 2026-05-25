/**
 * Rankings - live country intelligence view.
 */

import { useEffect, useState } from "react";
import { apiGet, CONFED_MAP } from "@/services/api";
import { FlagImg } from "@/components/FlagImg";
import { teamFlagCode } from "@/lib/flags";
import { USE_MOCKS } from "@/dev/devFlags";
import { getMockCountryRankings } from "@/dev/mockResponses";
import type { CountryRankingRow } from "@/contracts";
import { StandingsTable } from "@/components/tables/StandingsTable";
import { smartScoreBar, ratingBar } from "@/utils/statBar";

const CONFEDERATIONS = ["All", "UEFA", "CONMEBOL", "CONCACAF", "CAF", "AFC", "OFC"];

export default function RankingsPage() {
  const [conf, setConf] = useState("All");
  const [limit, setLimit] = useState(16);
  const [data, setData] = useState<CountryRankingRow[]>([]);
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(false);

  const handleConfChange = (nextConf: string) => {
    setLoading(true);
    setConf(nextConf);
  };

  const handleLimitChange = (nextLimit: number) => {
    setLoading(true);
    setLimit(nextLimit);
  };

  useEffect(() => {
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
        console.log('Team confederation fields:', rows.map((team) => ({ name: team.country_name, conf: team.confederation, confed: (team as CountryRankingRow & { confed?: string }).confed, region: (team as CountryRankingRow & { region?: string }).region, zone: (team as CountryRankingRow & { zone?: string }).zone })));
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
      <div className="wc-card" style={{ marginBottom: 18 }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 16, alignItems: "flex-start", flexWrap: "wrap" }}>
          <div style={{ display: "grid", gap: 10 }}>
            <div className="wc-eyebrow">Country intelligence</div>
            <h1 style={{ fontSize: "1.75rem", marginBottom: 0 }}>World rankings</h1>
            <p style={{ color: "var(--color-text-secondary)", fontSize: "0.875rem", maxWidth: 760, lineHeight: 1.7 }}>
              Rank countries by live backend strength, attack, defense, and form.
            </p>
          </div>
          <div className="wc-badge wc-badge-gold">{USE_MOCKS ? "DEV MOCKS" : "LIVE RANKINGS"}</div>
        </div>

        <div style={{ display: "flex", gap: 12, alignItems: "end", flexWrap: "wrap", marginTop: 16 }}>
          <div>
            <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "var(--color-text-secondary)", marginBottom: 4 }}>
              Confederation
            </label>
            <select className="select" value={conf} onChange={(e) => handleConfChange(e.target.value)}>
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
            <input type="range" min={8} max={64} value={limit} onChange={(e) => handleLimitChange(Number(e.target.value))} style={{ width: 160 }} />
          </div>
        </div>

        <div className="layout-3col" style={{ marginTop: 18 }}>
          {[
            { label: "Visible teams", value: data.length > 0 ? String(data.length) : "-" },
            { label: "Confederation", value: conf },
            { label: "Ranking depth", value: String(limit) },
          ].map((item) => (
            <div key={item.label} className="wc-stat-tile">
              <div className="metric">
                <span className="wc-stat-label">{item.label}</span>
                <span className="wc-stat-number" style={{ fontSize: "1.5rem" }}>{item.value}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="layout-3col" style={{ marginBottom: 18 }}>
        {data.slice(0, 3).map((row, index) => (
          <div key={row.country_uid} className="wc-card">
            <div className="wc-eyebrow">Top {index + 1}</div>
            <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "1.2rem", fontWeight: 800, marginBottom: 4 }}>
              <FlagImg code={teamFlagCode(row.country_uid) || teamFlagCode(row.country_name)} size={22} />
              <span>{row.country_name}</span>
            </div>
            <div style={{ color: "var(--color-text-secondary)", fontSize: "0.8125rem", marginBottom: 10 }}>
              {row.confederation ?? CONFED_MAP[row.country_name] ?? "Confederation not listed"}
            </div>
            <div style={{ display: "grid", gap: 8 }}>
              {[
                { label: "Smart Score", value: row.elo_rating, color: "var(--color-accent)" },
                { label: "Attack", value: row.attack_rating, color: "var(--color-green)" },
                { label: "Defense", value: row.defense_rating, color: "var(--color-gold)" },
              ].map((item) => (
                <div key={item.label}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                    <span style={{ fontSize: "0.75rem", color: "var(--color-text-secondary)" }}>{item.label}</span>
                    <span style={{ fontSize: "0.8rem", fontWeight: 700 }}>
                      {item.label === "Smart Score"
                        ? Number(item.value).toFixed(0)
                        : Number(item.value).toFixed(1)}
                    </span>
                  </div>
                  <div className="wc-odds-bar">
                    <div
                      className="wc-odds-fill odds-bar-fill"
                      style={{
                        width: `${item.label === "Smart Score" ? smartScoreBar(Number(item.value)) : ratingBar(Number(item.value))}%`,
                        background: item.color,
                      }}
                    />
                  </div>
                </div>
              ))}
              <div style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", marginTop: 2 }}>
                Form: {row.recent_form_score != null ? `${(Number(row.recent_form_score) * 100).toFixed(1)}%` : "-"} · Momentum: {row.momentum_score != null ? Number(row.momentum_score).toFixed(2) : "-"}
              </div>
            </div>
          </div>
        ))}
      </div>

      {note && (
        <div style={{ background: "rgba(111,168,255,0.08)", border: "1px solid rgba(111,168,255,0.2)", borderRadius: 10, padding: "8px 12px", fontSize: "0.8125rem", color: "var(--color-accent)", marginBottom: 12 }}>
          ℹ {note}
        </div>
      )}

      {loading && (
        <div style={{ padding: "16px 0", fontSize: "0.8125rem", color: "var(--color-text-secondary)" }}>
          <span className="spinner" style={{ marginRight: 8 }} /> Loading rankings...
        </div>
      )}

      <StandingsTable rows={data} title="Full table" />
    </div>
  );
}
