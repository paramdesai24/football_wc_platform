/**
 * Dashboard - live intelligence overview.
 */

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiGet } from "@/services/api";
import { USE_MOCKS } from "@/dev/devFlags";
import { getMockCountryRankings, getMockUpcomingPredictions } from "@/dev/mockResponses";
import type { CountryRankingRow, UpcomingPredictionRow } from "@/contracts";

interface HealthData {
  status?: string;
  version?: string;
  data_available?: boolean;
  endpoints?: Record<string, string>;
  [key: string]: unknown;
}

interface TournamentStatePreview {
  champion?: string;
  runner_up?: string;
  third_place?: string;
  matches?: Array<Record<string, unknown>>;
  group_standings?: Record<string, Array<Record<string, unknown>>>;
  [key: string]: unknown;
}

export default function DashboardPage() {
  const navigate = useNavigate();
  const [health, setHealth] = useState<HealthData | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [tournament, setTournament] = useState<TournamentStatePreview | null>(null);
  const [upcoming, setUpcoming] = useState<UpcomingPredictionRow[]>([]);
  const [upcomingNote, setUpcomingNote] = useState("");
  const [rankings, setRankings] = useState<CountryRankingRow[]>([]);
  const [rankingsNote, setRankingsNote] = useState("");

  useEffect(() => {
    apiGet<HealthData>("/health").then((res) => {
      if (res.error) {
        setHealthError(res.error);
      } else {
        setHealth(res.data ?? null);
      }
    });

    apiGet<{ data?: TournamentStatePreview }>("/api/v1/tournament_results?refresh=false").then((res) => {
      if (!res.error && res.data) {
        const state = Array.isArray(res.data) ? null : (res.data as { data?: TournamentStatePreview }).data;
        setTournament(state ?? null);
      }
    });

    apiGet<{ data?: UpcomingPredictionRow[] }>("/api/v1/predictions/upcoming").then((res) => {
      if (res.error || !res.data) {
        if (USE_MOCKS) {
          setUpcoming(getMockUpcomingPredictions());
          setUpcomingNote("Using dev mock upcoming matches.");
        } else {
          setUpcoming([]);
          setUpcomingNote("No live upcoming matches available.");
        }
        return;
      }

      const rows = Array.isArray(res.data) ? res.data : (res.data as { data?: UpcomingPredictionRow[] }).data;
      if (rows && rows.length > 0) {
        setUpcoming(rows);
        setUpcomingNote("");
      } else if (USE_MOCKS) {
        setUpcoming(getMockUpcomingPredictions());
        setUpcomingNote("Using dev mock upcoming matches.");
      } else {
        setUpcoming([]);
        setUpcomingNote("No live upcoming matches available.");
      }
    });

    apiGet<{ data?: CountryRankingRow[] }>("/api/v1/countries/rankings?limit=5").then((res) => {
      if (res.error || !res.data) {
        if (USE_MOCKS) {
          setRankings(getMockCountryRankings());
          setRankingsNote("Using dev mock rankings.");
        } else {
          setRankings([]);
          setRankingsNote("No live ranking preview available.");
        }
        return;
      }

      const rows = Array.isArray(res.data) ? res.data : (res.data as { data?: CountryRankingRow[] }).data;
      if (rows && rows.length > 0) {
        setRankings(rows);
        setRankingsNote("");
      } else if (USE_MOCKS) {
        setRankings(getMockCountryRankings());
        setRankingsNote("Using dev mock rankings.");
      } else {
        setRankings([]);
        setRankingsNote("No live ranking preview available.");
      }
    });
  }, []);

  const teamsTracked = rankings.length > 0 ? String(rankings.length) : "-";
  const featuredMatches = upcoming.length > 0 ? String(upcoming.length) : "-";
  const dataState = health?.data_available ? "Live" : healthError ? "Offline" : "Pending";
  const simulationState = health?.endpoints?.simulation ?? "Unknown";
  const topTeam = rankings[0]?.country_name ?? "Awaiting live ranking feed";
  const nextMatch = upcoming[0];

  return (
    <div className="page-container">
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="layout-hero">
          <div>
            <div className="section-kicker">
              World Cup intelligence
            </div>
            <h1 style={{ fontSize: "1.85rem", marginBottom: 10 }}>What is happening in the World Cup ecosystem right now?</h1>
            <p style={{ color: "var(--color-text-secondary)", maxWidth: 760, lineHeight: 1.65, marginBottom: 14 }}>
              Live backend rankings, tournament state, and prediction feeds are surfaced here first. Dev-only mock data stays explicit behind a flag.
            </p>
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
              <button className="btn btn-primary" onClick={() => navigate("/tournament")}>Open Tournament View</button>
              <button className="btn" onClick={() => navigate("/predictions")}>Open Predictor</button>
              <button className="btn" onClick={() => navigate("/rankings")}>Open Rankings</button>
            </div>
          </div>

          <div style={{ display: "grid", gap: 10 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12 }}>
              <div>
                <div style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", marginBottom: 4 }}>System</div>
                <div style={{ fontSize: "1rem", fontWeight: 700 }}>{healthError ? "Backend issue" : health?.status ?? "Checking"}</div>
              </div>
              <div className="badge badge-info">{USE_MOCKS ? "DEV MOCKS" : dataState}</div>
            </div>
            <div style={{ borderTop: "1px solid var(--color-border)", paddingTop: 10 }}>
              <div style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", marginBottom: 4 }}>Tournament state</div>
              <div style={{ fontWeight: 700 }}>{tournament?.champion ?? "Awaiting live simulation"}</div>
              <div style={{ fontSize: "0.8rem", color: "var(--color-text-secondary)", marginTop: 4 }}>
                Runner-up: {tournament?.runner_up ?? "TBD"}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="layout-2col" style={{ marginBottom: 16 }}>
        <div className="card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10, marginBottom: 14 }}>
            <div>
              <h2 style={{ fontSize: "1rem", marginBottom: 4 }}>Featured Match Intelligence</h2>
              <div style={{ color: "var(--color-text-muted)", fontSize: "0.8125rem" }}>Broadcast-style probability view</div>
            </div>
            <div className="badge badge-success">Live feed</div>
          </div>

          {nextMatch ? (
            <>
              <div style={{ display: "grid", gridTemplateColumns: "1.2fr 0.8fr", gap: 16, marginBottom: 12 }}>
                <div>
                  <div style={{ fontSize: "1.35rem", fontWeight: 800, marginBottom: 6 }}>{nextMatch.match}</div>
                  <div style={{ color: "var(--color-text-secondary)", fontSize: "0.85rem", lineHeight: 1.6 }}>
                    Current matchup pulled from the prediction engine and surfaced without frontend-derived odds.
                  </div>
                </div>
                <div style={{ display: "grid", gap: 8, alignContent: "start" }}>
                  <div>
                    <div style={{ fontSize: "0.72rem", color: "var(--color-text-muted)", marginBottom: 4 }}>Home win</div>
                    <div style={{ fontSize: "1.3rem", fontWeight: 800 }}>{nextMatch.home_win}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: "0.72rem", color: "var(--color-text-muted)", marginBottom: 4 }}>Draw</div>
                    <div style={{ fontSize: "1.3rem", fontWeight: 800 }}>{nextMatch.draw}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: "0.72rem", color: "var(--color-text-muted)", marginBottom: 4 }}>Away win</div>
                    <div style={{ fontSize: "1.3rem", fontWeight: 800 }}>{nextMatch.away_win}</div>
                  </div>
                </div>
              </div>

              <div className="layout-3col">
                {[
                  { label: "Top team", value: topTeam },
                  { label: "Featured matches", value: featuredMatches },
                  { label: "Backend version", value: health?.version ?? "-" },
                ].map((item) => (
                  <div key={item.label} className="card-compact">
                    <div className="metric">
                      <span className="metric-label">{item.label}</span>
                      <span className="metric-value" style={{ fontSize: "1rem" }}>{item.value}</span>
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div style={{ color: "var(--color-text-muted)", padding: "10px 0" }}>No upcoming match feed available.</div>
          )}
        </div>

        <div style={{ display: "grid", gap: 10 }}>
          <div className="card" style={{ minHeight: 118 }}>
            <div style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", marginBottom: 6 }}>System status</div>
            <div style={{ fontSize: "1.15rem", fontWeight: 800, marginBottom: 4 }}>{healthError ? "Backend offline" : health?.status ?? "Checking"}</div>
            <div style={{ color: "var(--color-text-secondary)", fontSize: "0.85rem", lineHeight: 1.6 }}>
              {health?.endpoints?.predictions ?? "Waiting on backend health response."}
            </div>
          </div>

          <div className="card" style={{ minHeight: 118 }}>
            <div style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", marginBottom: 6 }}>Simulation readiness</div>
            <div style={{ fontSize: "1.15rem", fontWeight: 800, marginBottom: 4 }}>{simulationState}</div>
            <div style={{ color: "var(--color-text-secondary)", fontSize: "0.85rem", lineHeight: 1.6 }}>
              Tournament results and play-as journeys remain driven by the backend simulation engine.
            </div>
          </div>
        </div>
      </div>

      {healthError && (
        <div className="card-compact" style={{ borderLeft: "3px solid var(--color-red)", marginBottom: 16 }}>
          <span style={{ color: "var(--color-red)", fontWeight: 600, fontSize: "0.8125rem" }}>
            Backend unreachable: {healthError}
          </span>
        </div>
      )}

      {upcomingNote && (
        <div style={{ background: "rgba(88,166,255,0.08)", border: "1px solid rgba(88,166,255,0.2)", borderRadius: 6, padding: "8px 12px", fontSize: "0.8125rem", color: "var(--color-accent)", marginBottom: 14 }}>
          ℹ {upcomingNote}
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 16, marginBottom: 16 }}>
        <div className="card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
            <h2 style={{ fontSize: "1rem" }}>Featured Matches</h2>
            <button className="btn" onClick={() => navigate("/predictions")}>Open Predictor</button>
          </div>
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Match</th>
                  <th className="text-center">Home Win</th>
                  <th className="text-center">Draw</th>
                  <th className="text-center">Away Win</th>
                </tr>
              </thead>
              <tbody>
                {upcoming.length > 0 ? (
                  upcoming.map((match) => (
                    <tr key={match.match}>
                      <td style={{ fontWeight: 600 }}>{match.match}</td>
                      <td className="text-center">{match.home_win}</td>
                      <td className="text-center">{match.draw}</td>
                      <td className="text-center">{match.away_win}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={4} style={{ color: "var(--color-text-muted)", padding: 16 }}>
                      No upcoming match feed available.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="card">
          <h2 style={{ fontSize: "1rem", marginBottom: 12 }}>Broadcast Notes</h2>
          <div style={{ display: "grid", gap: 12 }}>
            <div>
              <div style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", marginBottom: 4 }}>Intelligence story</div>
              <div style={{ fontWeight: 600 }}>{topTeam} remains the current reference point.</div>
            </div>
            <div>
              <div style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", marginBottom: 4 }}>Backend status</div>
              <div style={{ fontWeight: 600 }}>{health?.endpoints?.predictions ?? "Unknown"}</div>
            </div>
            <div>
              <div style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", marginBottom: 4 }}>Simulation readiness</div>
              <div style={{ fontWeight: 600 }}>{health?.endpoints?.simulation ?? "Unknown"}</div>
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
          <h2 style={{ fontSize: "1rem" }}>Rankings Preview</h2>
          <button className="btn" onClick={() => navigate("/rankings")}>Open Rankings</button>
        </div>
        {rankingsNote && (
          <div style={{ background: "rgba(88,166,255,0.08)", border: "1px solid rgba(88,166,255,0.2)", borderRadius: 6, padding: "8px 12px", fontSize: "0.8125rem", color: "var(--color-accent)", marginBottom: 12 }}>
            ℹ {rankingsNote}
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
              </tr>
            </thead>
            <tbody>
              {rankings.length > 0 ? (
                rankings.map((country) => (
                  <tr key={country.country_uid}>
                    <td>{country.rank}</td>
                    <td style={{ fontWeight: 600 }}>{country.country_name}</td>
                    <td className="text-right text-mono">{country.elo_rating}</td>
                    <td className="text-right text-mono">{country.attack_rating}</td>
                    <td className="text-right text-mono">{country.defense_rating}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} style={{ color: "var(--color-text-muted)", padding: 16 }}>
                    No live rankings available yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
