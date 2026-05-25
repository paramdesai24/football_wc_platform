import { parseMatchLabel, teamNameFromUid, teamFlagCode } from "@/lib/flags";
import { FlagImg } from "@/components/FlagImg";
import type { UpcomingPredictionRow } from "@/contracts";

interface FeaturedMatchCardProps {
  match: UpcomingPredictionRow;
  onOpenPredictions: () => void;
}

function clampScore(value: number): number {
  return Math.max(0, Math.min(4, value));
}

function formatProbability(value: number): string {
  return value > 0 ? `${value}%` : "—";
}

function trendLabel(homeWin: number, draw: number, awayWin: number): string {
  const gap = Math.max(homeWin, awayWin) - draw;
  if (gap >= 25) return "Clear edge";
  if (gap >= 12) return "Narrow edge";
  return "Tight fixture";
}

export function FeaturedMatchCard({ match, onOpenPredictions }: FeaturedMatchCardProps) {
  const parsed = parseMatchLabel(match.match);
  const homeName = teamNameFromUid(parsed.home);
  const awayName = teamNameFromUid(parsed.away);
  const homeWin = Number(match.home_win) || 0;
  const draw = Number(match.draw) || 0;
  const awayWin = Number(match.away_win) || 0;
  const hasForecast = homeWin > 0 || draw > 0 || awayWin > 0;
  const homeScore = hasForecast ? clampScore(Math.round(homeWin / 22)) : 0;
  const awayScore = hasForecast ? clampScore(Math.round(awayWin / 22)) : 0;
  const confidence = hasForecast ? Math.max(homeWin, awayWin, draw) : 0;

  const homePills = [
    { label: "Win", value: formatProbability(homeWin), tone: "wc-pill-gold" },
    { label: "Edge", value: formatProbability(Math.max(0, homeWin - draw)), tone: "wc-pill-blue" },
    { label: "Form", value: hasForecast ? trendLabel(homeWin, draw, awayWin) : "Awaiting data", tone: "wc-pill-green" },
  ];

  const awayPills = [
    { label: "Win", value: formatProbability(awayWin), tone: "wc-pill-gold" },
    { label: "Pressure", value: formatProbability(draw), tone: "wc-pill-blue" },
    { label: "Risk", value: hasForecast ? `${Math.max(0, 100 - confidence)}%` : "Awaiting", tone: "wc-pill-green" },
  ];

  return (
    <section className="wc-card">
      <div className="wc-card-header">
        <div className="wc-card-title-group">
          <div className="wc-eyebrow">Featured match</div>
          <h2 className="wc-section-title">Broadcast preview</h2>
        </div>
        <div className="wc-badge wc-badge-gold">Live forecast</div>
      </div>

      <div className="fixture-card" style={{ padding: 0, border: "none", background: "transparent" }}>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "minmax(0, 1fr) auto minmax(0, 1fr)",
            gap: 18,
            alignItems: "center",
          }}
        >
          <div style={{ display: "grid", gap: 12, justifyItems: "start" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
              <FlagImg code={teamFlagCode(parsed.home)} size={28} />
              <div>
                <div className="wc-team-name">{homeName}</div>
                <div className="wc-team-subtitle">Home side</div>
              </div>
            </div>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {homePills.map((pill) => (
                <span key={pill.label} className={`wc-pill ${pill.tone}`}>
                  {pill.label} {pill.value}
                </span>
              ))}
            </div>
          </div>

          <div style={{ textAlign: "center", minWidth: 150 }}>
            <div className="wc-mono" style={{ fontSize: "3rem", lineHeight: 1, fontWeight: 700, color: "var(--color-text)" }}>
              {hasForecast ? `${homeScore} - ${awayScore}` : "TBD"}
            </div>
            <div style={{ marginTop: 10, display: "grid", justifyItems: "center", gap: 8 }}>
              <span className="wc-badge wc-badge-gold">{hasForecast ? `${confidence}% confidence` : "Forecast pending"}</span>
              <span className="wc-pill wc-pill-blue">{hasForecast ? trendLabel(homeWin, draw, awayWin) : "Waiting on live data"}</span>
            </div>
          </div>

          <div style={{ display: "grid", gap: 12, justifyItems: "end" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 14, justifyContent: "flex-end" }}>
              <div style={{ textAlign: "right" }}>
                <div className="wc-team-name">{awayName}</div>
                <div className="wc-team-subtitle">Away side</div>
              </div>
              <FlagImg code={teamFlagCode(parsed.away)} size={28} />
            </div>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", justifyContent: "flex-end" }}>
              {awayPills.map((pill) => (
                <span key={pill.label} className={`wc-pill ${pill.tone}`}>
                  {pill.label} {pill.value}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div
        style={{
          marginTop: 16,
          paddingTop: 14,
          borderTop: "1px solid rgba(255,255,255,0.08)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 12,
          flexWrap: "wrap",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
          <span className="wc-badge">Upcoming fixture</span>
          <span className="wc-pill">Live projection</span>
          <span style={{ color: "var(--color-text-secondary)", fontSize: "0.85rem" }}>{match.match}</span>
        </div>
        <button className="btn btn-primary" onClick={onOpenPredictions}>
          Explore Predictions
        </button>
      </div>
    </section>
  );
}
