import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { CountryRankingRow, UpcomingPredictionRow } from "@/contracts";
import { apiGet } from "@/services/api";
import { USE_MOCKS } from "@/dev/devFlags";
import { getMockCountryRankings, getMockUpcomingPredictions } from "@/dev/mockResponses";
import { FlagImg } from "@/components/FlagImg";
import { teamFlagCode } from "@/lib/flags";
import { FeaturedMatchCard } from "@/components/cards/FeaturedMatchCard";
import { StandingsTable } from "@/components/tables/StandingsTable";
import { SpringCard } from "@/components/ui/SpringCard";

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

function percent(n: number): string {
  return `${Math.round(n)}%`;
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

    apiGet<{ data?: CountryRankingRow[] }>("/api/v1/countries/rankings?limit=16").then((res) => {
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

  const dataState = health?.data_available ? "Live" : healthError ? "Offline" : "Pending";
  const simulationState = health?.endpoints?.simulation ?? "Unknown";
  const topTeam = rankings[0]?.country_name ?? "Awaiting live ranking feed";
  const nextMatch = upcoming[0];
  const topRankings = rankings.slice(0, 8);
  const topStandings = rankings.slice(0, 12);
  const topElo = topRankings[0]?.elo_rating ?? 1;

  useEffect(() => {
    if (topRankings.length > 0) {
      console.log("Championship odds raw data:", topRankings);
    }
  }, [topRankings]);
  const topMover = [...rankings]
    .sort((a, b) => (b.recent_form_score ?? 0) - (a.recent_form_score ?? 0))[0]?.country_name ?? topTeam;
  const activeSimulations = tournament?.matches?.length ?? 0;
  const volatilityIndex = rankings.length > 1 ? Math.round(Math.abs((rankings[0]?.elo_rating ?? 0) - (rankings[Math.min(5, rankings.length - 1)]?.elo_rating ?? 0)) / 10) : 0;
  const qualificationTension = rankings.length > 8 ? Math.round(Math.max(0, (rankings[7]?.elo_rating ?? 0) - (rankings[11]?.elo_rating ?? 0)) / 10) : 0;

  return (
    <div className="page-content">
      <SpringCard
        className="wc-card"
        delay={0}
        style={{
          minHeight: "calc(100vh - 124px)",
          display: "grid",
          alignItems: "center",
          textAlign: "center",
          padding: "48px 28px 40px",
          marginBottom: 22,
        }}
      >
        <div style={{ maxWidth: 980, margin: "0 auto", display: "grid", gap: 22, justifyItems: "center" }}>
          <div className="wc-badge wc-badge-gold">FIFA WORLD CUP 2026 · INTELLIGENCE PLATFORM</div>
          <div style={{ display: "grid", gap: 12, justifyItems: "center" }}>
            <h1 className="wc-hero-title">The World Cup, Decoded.</h1>
            <p style={{ maxWidth: 820, margin: 0, color: "var(--color-text-secondary)", fontSize: "1.125rem", lineHeight: 1.7 }}>
              AI-powered predictions, match simulations, and tournament intelligence.
            </p>
          </div>

          <div style={{ display: "flex", gap: 12, flexWrap: "wrap", justifyContent: "center" }}>
            <button className="btn btn-primary" onClick={() => navigate("/predictions")}>Explore Predictions</button>
            <button className="btn btn-green" onClick={() => navigate("/rankings")}>Live Standings</button>
          </div>

          <div className="layout-3col" style={{ width: "100%", maxWidth: 760 }}>
            {[
              { label: "Live feed", value: dataState },
              { label: "Top team", value: <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}><FlagImg code={teamFlagCode(topTeam)} size={18} /><span>{topTeam}</span></span> },
              { label: "Next fixture", value: nextMatch ? nextMatch.match : "Awaiting schedule" },
            ].map((item) => (
              <div key={item.label} className="wc-stat-tile">
                <div className="wc-stat-number" style={{ fontSize: "1.75rem" }}>{item.value}</div>
                <div className="wc-stat-label" style={{ marginTop: 6 }}>{item.label}</div>
              </div>
            ))}
          </div>
        </div>
      </SpringCard>

      {upcomingNote && (
        <div style={{ marginBottom: 14, background: "rgba(212, 175, 55, 0.08)", border: "1px solid rgba(212, 175, 55, 0.18)", borderRadius: 12, padding: "10px 12px", color: "#f4e1a0", fontSize: "0.875rem" }}>
          ℹ {upcomingNote}
        </div>
      )}

      {nextMatch ? (
        <SpringCard delay={100} style={{ marginBottom: 22 }}>
          <FeaturedMatchCard match={nextMatch} onOpenPredictions={() => navigate("/predictions")} />
        </SpringCard>
      ) : (
        <SpringCard delay={100} className="wc-card" style={{ marginBottom: 22 }}>
          <div className="wc-card-header">
            <div className="wc-card-title-group">
              <div className="wc-eyebrow">Featured match</div>
              <h2 className="wc-section-title">Broadcast preview</h2>
            </div>
          </div>
          <div style={{ color: "var(--color-text-muted)" }}>No upcoming match feed available.</div>
        </SpringCard>
      )}

      <div className="layout-2col">
        <SpringCard className="wc-card" delay={150}>
          <div className="wc-card-header">
            <div className="wc-card-title-group">
              <div className="wc-eyebrow">Championship odds</div>
              <h2 className="wc-section-title">Title race leaders</h2>
              <div className="card-subtitle">Based on current rankings strength · Win probability proxy</div>
            </div>
            <div className="wc-badge">Top 8</div>
          </div>
          <div style={{ display: "grid", gap: 12 }}>
            {topRankings.length > 0 ? (
              topRankings.map((row, index) => {
                const chance = Math.min(35, Math.max(8, Math.round((row.elo_rating / topElo) * 35)));
                const scaledWidth = `${(chance / 35) * 100}%`;
                const barColor = row.rank === 1 ? "#d4af37" : row.rank <= 3 ? "#22c55e" : row.rank <= 6 ? "#3b82f6" : "rgba(255,255,255,0.25)";
                const rankIcon = row.rank === 1 ? "🏆" : row.rank === 2 ? "🥈" : row.rank === 3 ? "🥉" : "";
                return (
                  <div key={row.country_uid} className={`stagger-item delay-${Math.min(index, 10)}`} style={{ display: "grid", gap: 8 }}>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 10, minWidth: 0 }}>
                        <span style={{ fontSize: 18 }}>{rankIcon}</span>
                        <FlagImg code={teamFlagCode(row.country_name)} size={18} />
                        <span style={{ fontWeight: 700, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{row.country_name}</span>
                      </div>
                      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                        {index === 0 ? <span className="wc-badge wc-badge-gold">#1</span> : <span className="wc-pill">#{index + 1}</span>}
                        <span className="wc-mono num-md">{percent(chance)}</span>
                      </div>
                    </div>
                    <div className="wc-odds-bar">
                      <div className="wc-odds-fill odds-bar-fill" style={{ width: scaledWidth, background: barColor }} />
                    </div>
                  </div>
                );
              })
            ) : (
              <div style={{ color: "var(--color-text-muted)" }}>No live odds available yet.</div>
            )}
          </div>
        </SpringCard>

        <SpringCard className="wc-card" delay={200}>
          <div className="wc-card-header">
            <div className="wc-card-title-group">
              <div className="wc-eyebrow">Tournament pulse</div>
              <h2 className="wc-section-title">Live tension indicators</h2>
            </div>
            <div className="wc-badge wc-badge-gold">{simulationState}</div>
          </div>

          <div className="wc-stat-grid">
            {[
              { label: "Active simulations", value: activeSimulations },
              { label: "Volatility index", value: volatilityIndex },
              { label: "Qualification tension", value: qualificationTension },
              { label: "Top mover", value: <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}><FlagImg code={teamFlagCode(topMover)} size={18} /><span>{topMover}</span></span> },
            ].map((item) => (
              <div key={item.label} className="wc-stat-tile">
                <div className="wc-stat-number">{item.value}</div>
                <div className="wc-stat-label" style={{ marginTop: 6 }}>{item.label}</div>
              </div>
            ))}
          </div>
        </SpringCard>
      </div>

      <SpringCard delay={250} style={{ marginBottom: 22 }}>
        <StandingsTable
          rows={topStandings}
          title="Current standings"
          subtitle={rankingsNote || undefined}
          onOpenRankings={() => navigate("/rankings")}
        />
      </SpringCard>

      {healthError && (
        <div className="wc-card" style={{ marginBottom: 16, borderLeft: "3px solid var(--wc-red)" }}>
          <span style={{ color: "#ffb3ae", fontWeight: 600, fontSize: "0.875rem" }}>Backend unreachable: {healthError}</span>
        </div>
      )}

      {health?.data_available === false && !healthError && (
        <div className="wc-card" style={{ marginBottom: 16, borderLeft: "3px solid var(--wc-gold)" }}>
          <span style={{ color: "#f4e1a0", fontWeight: 600, fontSize: "0.875rem" }}>Backend is responding, but live data is not yet marked available.</span>
        </div>
      )}
    </div>
  );
}
