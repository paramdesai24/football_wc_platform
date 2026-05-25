import { smartScoreBar } from "@/utils/statBar";

const simulationSteps = [
  {
    title: "Build the team state",
    body: "The backend loads the processed rankings and team data, then builds a live team_state snapshot for every nation before the tournament starts.",
  },
  {
    title: "Simulate group matches",
    body: "Each group match is predicted through the match engine, xG is converted into goals with Poisson sampling when stochastic mode is on, and the standings are updated immediately.",
  },
  {
    title: "Resolve knockout drama",
    body: "Knockout matches move through regulation, extra time, and penalties so every bracket path ends with a winner.",
  },
  {
    title: "Repeat at scale",
    body: "The tournament can run once for a saved state, 2 quick runs for refreshes, 3 for overrides, or 100 simulations for a fuller Monte Carlo pass.",
  },
];

const smartScoreSignals = [
  "Elo rating from the processed country rankings",
  "Attack and defense ratings from the ranking dataset",
  "Recent form, momentum, consistency, and squad strength in the backend data pipeline",
  "The frontend does not recalculate the score; it displays the backend's elo_rating field and scales it for the bar",
];

function MetricBar({ label, value, fill, tone }: { label: string; value: string; fill: number; tone: string }) {
  return (
    <div className="wc-card stat-card" style={{ padding: 18 }}>
      <div className="stat-card-top">
        <div className="stat-label">{label}</div>
        <div className="stat-value" style={{ fontSize: 24 }}>{value}</div>
      </div>
      <div className="stat-bar-track">
        <div className="stat-bar-fill" style={{ width: `${fill}%`, background: tone }} />
      </div>
    </div>
  );
}

export default function AboutPage() {
  return (
    <div className="page-container">
      <section className="wc-card section-card" style={{ marginBottom: 18 }}>
        <div className="wc-card-header" style={{ marginBottom: 0 }}>
          <div className="wc-card-title-group">
            <div className="eyebrow">System guide</div>
            <h1 className="page-title" style={{ fontSize: "1.9rem", marginBottom: 0 }}>How FC Analytics works</h1>
            <p className="page-sub" style={{ maxWidth: 820, margin: 0 }}>
              This page explains the backend simulation flow, where the Smart Score comes from, and how the website turns raw football data into the views you see in the app.
            </p>
          </div>
          <div className="wc-badge wc-badge-gold">LIVE BACKEND LOGIC</div>
        </div>
      </section>

      <div className="layout-2col" style={{ marginBottom: 18 }}>
        <section className="wc-card">
          <div className="wc-card-header">
            <div className="wc-card-title-group">
              <div className="eyebrow">Backend simulation logic</div>
              <h2 className="wc-section-title">How tournaments are generated</h2>
            </div>
            <div className="wc-badge">Monte Carlo</div>
          </div>

          <div style={{ display: "grid", gap: 12 }}>
            {simulationSteps.map((step, index) => (
              <div key={step.title} className="card-compact" style={{ borderColor: "rgba(255,255,255,0.08)", background: "rgba(255,255,255,0.03)" }}>
                <div style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
                  <div className="wc-badge wc-badge-gold" style={{ minWidth: 32, justifyContent: "center" }}>{index + 1}</div>
                  <div style={{ display: "grid", gap: 4 }}>
                    <div style={{ fontWeight: 800, fontSize: "0.98rem" }}>{step.title}</div>
                    <div style={{ color: "var(--color-text-secondary)", lineHeight: 1.65, fontSize: "0.9rem" }}>{step.body}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="wc-card">
          <div className="wc-card-header">
            <div className="wc-card-title-group">
              <div className="eyebrow">Smart Score</div>
              <h2 className="wc-section-title">What the number actually means</h2>
            </div>
            <div className="wc-badge wc-badge-gold">Elo-backed</div>
          </div>

          <div style={{ display: "grid", gap: 14 }}>
            <div className="card-compact" style={{ borderColor: "rgba(212,175,55,0.16)", background: "rgba(212,175,55,0.06)" }}>
              <div style={{ fontSize: "0.9rem", lineHeight: 1.7, color: "var(--color-text-secondary)" }}>
                In the current UI, Smart Score is the backend <strong>elo_rating</strong> value returned by the country rankings endpoint. The frontend only formats it and converts it into a progress bar.
              </div>
            </div>

            <div className="layout-3col">
              <MetricBar label="Low" value="1600" fill={smartScoreBar(1600)} tone="var(--color-red)" />
              <MetricBar label="Mid" value="1900" fill={smartScoreBar(1900)} tone="var(--color-accent)" />
              <MetricBar label="High" value="2200" fill={smartScoreBar(2200)} tone="var(--color-green)" />
            </div>

            <div className="card-compact" style={{ background: "rgba(255,255,255,0.03)" }}>
              <div style={{ fontWeight: 700, marginBottom: 8 }}>The scaling logic</div>
              <div style={{ color: "var(--color-text-secondary)", lineHeight: 1.7, fontSize: "0.9rem" }}>
                The bar uses a fixed range from 1600 to 2200. Anything below 1600 clamps to 0%, anything above 2200 clamps to 100%. That keeps the visual consistent even when the underlying rating changes.
              </div>
            </div>
          </div>
        </section>
      </div>

      <div className="layout-2col" style={{ marginBottom: 18 }}>
        <section className="wc-card">
          <div className="wc-card-header">
            <div className="wc-card-title-group">
              <div className="eyebrow">What feeds it</div>
              <h2 className="wc-section-title">The data the website uses</h2>
            </div>
            <div className="wc-badge">Rankings feed</div>
          </div>

          <div style={{ display: "grid", gap: 10 }}>
            {smartScoreSignals.map((signal) => (
              <div key={signal} className="card-compact" style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
                <span style={{ color: "var(--color-accent)", fontWeight: 800 }}>•</span>
                <div style={{ color: "var(--color-text-secondary)", lineHeight: 1.65, fontSize: "0.9rem" }}>{signal}</div>
              </div>
            ))}
          </div>
        </section>

        <section className="wc-card">
          <div className="wc-card-header">
            <div className="wc-card-title-group">
              <div className="eyebrow">How the site works</div>
              <h2 className="wc-section-title">Where each page gets its data</h2>
            </div>
            <div className="wc-badge wc-badge-gold">API-driven</div>
          </div>

          <div style={{ display: "grid", gap: 10 }}>
            <div className="card-compact">Dashboard, Rankings, Analytics, and Predictions read live backend endpoints.</div>
            <div className="card-compact">Tournament Simulation calls the tournament orchestrator, which runs the whole bracket.</div>
            <div className="card-compact">Play As A Team runs the simulation multiple times and extracts one team’s journey from each run.</div>
            <div className="card-compact">The navbar and route structure are shared across the entire app, so the theme and navigation stay consistent.</div>
          </div>
        </section>
      </div>

      <section className="wc-card" style={{ marginBottom: 18 }}>
        <div className="wc-card-header">
          <div className="wc-card-title-group">
            <div className="eyebrow">In plain language</div>
            <h2 className="wc-section-title">Why results can change between runs</h2>
          </div>
          <div className="wc-badge">Seeded randomness</div>
        </div>

        <div style={{ color: "var(--color-text-secondary)", lineHeight: 1.75, fontSize: "0.95rem", maxWidth: 980 }}>
          The simulation is intentionally not deterministic. The backend uses the same underlying football intelligence every time, but it samples outcomes to reflect match variance. That is why a strong team can still lose a single run, while its longer-term probability remains high across repeated simulations.
        </div>
      </section>
    </div>
  );
}