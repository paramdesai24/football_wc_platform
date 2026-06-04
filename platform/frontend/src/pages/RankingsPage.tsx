/**
 * Rankings – live country intelligence view. Hard-capped at 40 countries.
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
import { EmptyState } from "@/components/ui/EmptyState";

const CONFEDERATIONS = ["All", "UEFA", "CONMEBOL", "CONCACAF", "CAF", "AFC", "OFC"];
const MAX_COUNTRIES = 40;

export default function RankingsPage() {
  const [conf, setConf] = useState("All");
  const [limit, setLimit] = useState(20);
  const [data, setData] = useState<CountryRankingRow[]>([]);
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(true);

  const handleConfChange = (nextConf: string) => {
    setLoading(true);
    setConf(nextConf);
  };

  const handleLimitChange = (nextLimit: number) => {
    setLoading(true);
    setLimit(Math.min(nextLimit, MAX_COUNTRIES));
  };

  useEffect(() => {
    const confParam = conf === "All" ? "" : conf;
    const safeLimit = Math.min(limit, MAX_COUNTRIES);

    apiGet<{ data?: CountryRankingRow[] }>(
      `/api/v1/countries/rankings?confederation=${confParam}&limit=${safeLimit}`
    ).then((res) => {
      setLoading(false);

      if (res.error || !res.data) {
        if (USE_MOCKS) {
          setData(getMockCountryRankings().slice(0, safeLimit));
          setNote("Using dev mock rankings.");
        } else {
          setData([]);
          setNote("No live rankings available.");
        }
        return;
      }

      const rows = Array.isArray(res.data)
        ? res.data
        : (res.data as { data?: CountryRankingRow[] }).data;

      if (rows && rows.length > 0) {
        setData(rows.slice(0, MAX_COUNTRIES));
        setNote("");
      } else if (USE_MOCKS) {
        setData(getMockCountryRankings().slice(0, safeLimit));
        setNote("Using dev mock rankings.");
      } else {
        setData([]);
        setNote("No live rankings available.");
      }
    });
  }, [conf, limit]);

  return (
    <div className="page-content">

      {/* ── Header card ─────────────────────────────────────────── */}
      <div className="wc-card" style={{ marginBottom: 18 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 16 }}>
          <div>
            <div className="wc-eyebrow">Country Intelligence</div>
            <h1 style={{ fontSize: "1.75rem", fontWeight: 800, marginBottom: 6 }}>World Rankings</h1>
          </div>
          <div className={`wc-badge ${USE_MOCKS ? "" : "wc-badge-gold"}`}>
            {USE_MOCKS ? "DEV MOCKS" : "LIVE RANKINGS"}
          </div>
        </div>

        {/* ── Filters ─────────────────────────────────────────── */}
        <div style={{ display: "flex", gap: 24, alignItems: "flex-end", flexWrap: "wrap", marginTop: 20 }}>

          {/* Confederation select */}
          <div>
            <label style={{ display: "block", fontSize: "0.7rem", fontWeight: 700, color: "var(--color-text-secondary)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 6 }}>
              Confederation
            </label>
            <select className="select" value={conf} onChange={(e) => handleConfChange(e.target.value)}>
              {CONFEDERATIONS.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          {/* Depth slider — hard max 40 */}
          <div style={{ minWidth: 220 }}>
            <label style={{ display: "block", fontSize: "0.7rem", fontWeight: 700, color: "var(--color-text-secondary)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 6 }}>
              Show top{" "}
              <span style={{ color: "var(--color-gold)", fontWeight: 800, fontSize: "0.85rem" }}>
                {limit}
              </span>
              {" "}of {MAX_COUNTRIES}
            </label>
            <input
              type="range"
              min={5}
              max={MAX_COUNTRIES}
              step={5}
              value={limit}
              onChange={(e) => handleLimitChange(Number(e.target.value))}
              style={{ width: "100%", accentColor: "var(--color-gold)" }}
            />
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.65rem", color: "var(--color-text-muted)", marginTop: 2 }}>
              <span>5</span>
              <span>40 max</span>
            </div>
          </div>
        </div>

        {/* ── Summary stat tiles ───────────────────────────────── */}
        <div className="layout-3col" style={{ marginTop: 18 }}>
          {[
            { label: "Visible teams", value: loading ? "…" : String(data.length) },
            { label: "Confederation", value: conf },
            { label: "Ranking depth", value: `Top ${limit}` },
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

      {/* ── Podium — top 3 cards ─────────────────────────────────── */}
      {data.slice(0, 3).length > 0 && (
        <div className="layout-3col" style={{ marginBottom: 18 }}>
          {data.slice(0, 3).map((row, index) => (
            <div key={row.country_uid} className="wc-card">
              <div className="wc-eyebrow">Top {index + 1}</div>
              <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "1.15rem", fontWeight: 800, marginBottom: 4 }}>
                <FlagImg code={teamFlagCode(row.country_uid) || teamFlagCode(row.country_name)} size={22} />
                <span>{row.country_name}</span>
              </div>
              <div style={{ color: "var(--color-text-secondary)", fontSize: "0.8125rem", marginBottom: 12 }}>
                {row.confederation ?? CONFED_MAP[row.country_name] ?? "—"}
              </div>

              <div style={{ display: "grid", gap: 10 }}>
                {[
                  { label: "Smart Score", value: row.overall_rank_score != null ? row.overall_rank_score * 100 : row.elo_rating, color: "var(--color-accent)", isComposite: row.overall_rank_score != null },
                  { label: "Attack",       value: row.attack_rating,  color: "var(--color-green)", isComposite: false },
                  { label: "Defense",      value: row.defense_rating, color: "var(--color-gold)",  isComposite: false },
                ].map((item) => (
                  <div key={item.label}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                      <span style={{ fontSize: "0.72rem", color: "var(--color-text-secondary)", textTransform: "uppercase", letterSpacing: "0.06em", fontWeight: 600 }}>{item.label}</span>
                      <span style={{ fontSize: "0.82rem", fontWeight: 700, color: item.color }}>{Number(item.value).toFixed(1)}</span>
                    </div>
                    <div className="wc-odds-bar">
                      <div
                        className="wc-odds-fill"
                        style={{
                          width: `${item.isComposite
                            ? Math.min(100, Number(item.value))
                            : item.label === "Smart Score"
                              ? smartScoreBar(Number(item.value))
                              : ratingBar(Number(item.value))}%`,
                          background: item.color,
                          transition: "width 0.5s ease",
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>

              <div style={{ fontSize: "0.72rem", color: "var(--color-text-muted)", marginTop: 10, display: "flex", gap: 10 }}>
                <span>Form: {row.recent_form_score != null ? `${(Number(row.recent_form_score) * 100).toFixed(1)}%` : "—"}</span>
                <span>·</span>
                <span>Momentum: {row.momentum_score != null ? Number(row.momentum_score).toFixed(2) : "—"}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── Note banner ─────────────────────────────────────────── */}
      {note && (
        <div style={{
          background: "rgba(111,168,255,0.08)",
          border: "1px solid rgba(111,168,255,0.2)",
          borderRadius: 10,
          padding: "8px 14px",
          fontSize: "0.8125rem",
          color: "var(--color-accent)",
          marginBottom: 12,
        }}>
          ℹ {note}
        </div>
      )}

      {/* ── Loading indicator ────────────────────────────────────── */}
      {loading && (
        <div style={{ padding: "14px 0", fontSize: "0.8125rem", color: "var(--color-text-secondary)", display: "flex", alignItems: "center", gap: 8 }}>
          <span className="spinner" />
          Loading rankings…
        </div>
      )}

      {/* ── Full table ──────────────────────────────────────────── */}
      {data.length === 0 && !loading ? (
        <EmptyState
          icon="📊"
          title="No rankings yet"
          description="No data for this filter. Try a different confederation or increase the depth slider."
        />
      ) : (
        <div className="table-scroll-wrapper">
          <StandingsTable rows={data} title={`Full table — Top ${data.length}`} />
        </div>
      )}
    </div>
  );
}
