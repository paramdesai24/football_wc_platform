import { smartScoreBar } from "@/utils/statBar";

const simulationSteps = [
  {
    title: "Predictive Nation Modeling",
    body: "The engine initializes a comprehensive performance profile for all 48 qualified countries, capturing Elo rating, attack/defense coefficients, and momentum trends before kickoff.",
  },
  {
    title: "Stochastic Match Simulation",
    body: "Each fixture resolves through a dynamic expected-goals (xG) matrix. For stochastic modes, Poisson distribution modeling translates these strengths into realistic scorelines.",
  },
  {
    title: "Tournament Bracket Orchestration",
    body: "From the group stage standings, the engine automatically paths qualified teams through regulation, extra time, and penalty shootouts to simulate the full tournament tree.",
  },
  {
    title: "Monte Carlo Probability Scaling",
    body: "To model unpredictability, simulations can scale from single-run brackets up to 100-run Monte Carlo passes, yielding robust winning probabilities and dark horse insights.",
  },
];

const smartScoreSignals = [
  "Historical Elo ratings derived from all international fixtures.",
  "Calibrated attack and defense coefficients based on tournament data.",
  "Recent form indexes, team momentum, and overall squad depth.",
  "Confederation weighting to account for international competition strength.",
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
  const card: React.CSSProperties = {
    background: 'rgba(10,18,34,0.72)',
    backdropFilter: 'blur(16px)',
    border: '1px solid rgba(255,255,255,0.09)',
    borderRadius: 16,
    padding: '24px 28px',
  };

  const itemCard: React.CSSProperties = {
    background: 'rgba(255,255,255,0.03)',
    border: '1px solid rgba(255,255,255,0.06)',
    borderRadius: 12,
    padding: '16px 20px',
  };

  return (
    <div className="page-container" style={{ display: "grid", gap: 18 }}>
      
      {/* Hero Header */}
      <section className="wc-card section-card" style={{ padding: "32px 36px" }}>
        <div className="wc-card-header" style={{ marginBottom: 0, display: "flex", justifyContent: "space-between", gap: 20, alignItems: "flex-start", flexWrap: "wrap" }}>
          <div className="wc-card-title-group" style={{ display: "grid", gap: 8 }}>
            <div className="eyebrow" style={{ color: "#d4af37" }}>Methodology & Engine Insights</div>
            <h1 className="page-title" style={{ fontSize: "clamp(2rem, 4vw, 2.5rem)", marginBottom: 0 }}>How FC Analytics Works</h1>
            <p className="page-sub" style={{ maxWidth: 820, margin: 0 }}>
              An overview of our tournament simulator, the mathematical models behind the Smart Score, and how we deliver real-time calculations.
            </p>
          </div>
          <span className="wc-badge wc-badge-gold" style={{ padding: "6px 14px", fontSize: 11, fontWeight: 700 }}>PREMIUM SIMULATION ENGINE</span>
        </div>
      </section>

      {/* Main Grid */}
      <div className="layout-2col" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18 }}>
        
        {/* Tournament Simulator */}
        <section style={card}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
            <div>
              <div className="eyebrow">Simulation algorithm</div>
              <h2 className="wc-section-title" style={{ margin: 0, fontSize: 20 }}>Tournament Forecasting</h2>
            </div>
            <span className="wc-badge" style={{ background: "rgba(255,255,255,0.08)", color: "#fff", fontSize: 11 }}>Monte Carlo Model</span>
          </div>

          <div style={{ display: "grid", gap: 14 }}>
            {simulationSteps.map((step, index) => (
              <div key={step.title} style={itemCard}>
                <div style={{ display: "flex", alignItems: "flex-start", gap: 14 }}>
                  <div style={{
                    width: 32,
                    height: 32,
                    borderRadius: "50%",
                    background: "rgba(212,175,55,0.12)",
                    border: "1px solid rgba(212,175,55,0.3)",
                    color: "#d4af37",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontWeight: 800,
                    fontSize: 13,
                    flexShrink: 0
                  }}>{index + 1}</div>
                  <div style={{ display: "grid", gap: 4 }}>
                    <div style={{ fontWeight: 800, fontSize: "1rem", color: "#fff" }}>{step.title}</div>
                    <div style={{ color: "var(--color-text-secondary)", lineHeight: 1.6, fontSize: 13 }}>{step.body}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Smart Score */}
        <section style={card}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
            <div>
              <div className="eyebrow">Nation index</div>
              <h2 className="wc-section-title" style={{ margin: 0, fontSize: 20 }}>Understanding Smart Score</h2>
            </div>
            <span className="wc-badge wc-badge-gold" style={{ fontSize: 11 }}>Elo-Backed</span>
          </div>

          <div style={{ display: "grid", gap: 16 }}>
            <div style={{ ...itemCard, background: "rgba(212,175,55,0.04)", borderColor: "rgba(212,175,55,0.15)" }}>
              <div style={{ fontSize: 13, lineHeight: 1.65, color: "rgba(255,255,255,0.8)" }}>
                The <strong>Smart Score</strong> is our composite rating metric. It evaluates team strength on a scaled index derived directly from the nation rankings, providing a standardized gauge of competitiveness.
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10 }}>
              <MetricBar label="Emerging" value="1600" fill={smartScoreBar(1600)} tone="var(--color-red)" />
              <MetricBar label="Competitive" value="1900" fill={smartScoreBar(1900)} tone="var(--color-accent)" />
              <MetricBar label="Contender" value="2200" fill={smartScoreBar(2200)} tone="var(--color-green)" />
            </div>

            <div style={itemCard}>
              <div style={{ fontWeight: 800, marginBottom: 6, color: "#fff", fontSize: 14 }}>Scaling & Normalization</div>
              <div style={{ color: "var(--color-text-secondary)", lineHeight: 1.6, fontSize: 13 }}>
                To maintain a clean visual comparison, raw ratings are mapped into a standardized range. This scale accommodates team performance fluctuations while ensuring data visualizations remain consistent and intuitive.
              </div>
            </div>
          </div>
        </section>
      </div>

      {/* Realtime Draft & Auction */}
      <section style={card}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
          <div>
            <div className="eyebrow">Realtime gameplay</div>
            <h2 className="wc-section-title" style={{ margin: 0, fontSize: 20 }}>Realtime Auction Engine</h2>
          </div>
          <span className="wc-badge" style={{ background: "rgba(34,197,94,0.12)", color: "#22c55e", fontSize: 11 }}>Synchronized Room</span>
        </div>

        <div style={{ display: "grid", gap: 14 }}>
          <div style={{ color: "var(--color-text-secondary)", lineHeight: 1.65, fontSize: 14 }}>
            The auction system allows managers to draft their dream World Cup squads dynamically. Bidding, nominations, timer resets, and roster requirements are synchronized instantaneously across all active participants using high-speed network connections.
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: 14 }}>
            <div style={itemCard}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                <span style={{ fontSize: 18 }}>⏱️</span>
                <strong style={{ color: "#fff", fontSize: 14 }}>Active Bidding</strong>
              </div>
              <div style={{ color: "var(--color-text-secondary)", fontSize: 12.5, lineHeight: 1.55 }}>
                Nominations run through a 60-second window. Once the first bid is accepted, the timer is shortened to a 30-second window, which resets on every subsequent bid.
              </div>
            </div>

            <div style={itemCard}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                <span style={{ fontSize: 18 }}>📋</span>
                <strong style={{ color: "#fff", fontSize: 14 }}>Roster Constraints</strong>
              </div>
              <div style={{ color: "var(--color-text-secondary)", fontSize: 12.5, lineHeight: 1.55 }}>
                Position minimums (3 GK, 5 DEF, 5 MID, 5 FWD) and squad limits (max 20) are automatically verified during live bidding to prevent invalid squad compositions.
              </div>
            </div>

            <div style={itemCard}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                <span style={{ fontSize: 18 }}>🏆</span>
                <strong style={{ color: "#fff", fontSize: 14 }}>Best XI Points</strong>
              </div>
              <div style={{ color: "var(--color-text-secondary)", fontSize: 12.5, lineHeight: 1.55 }}>
                Individual player scores compile automatically. Your total league score is derived strictly from the top 11 players in your squad matching a 1-4-3-3 formation.
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Data Feeds & Randomness */}
      <div className="layout-2col" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18 }}>
        <section style={card}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
            <div>
              <div className="eyebrow">Input parameters</div>
              <h2 className="wc-section-title" style={{ margin: 0, fontSize: 20 }}>Underlying Analytics Feed</h2>
            </div>
            <span className="wc-badge" style={{ background: "rgba(255,255,255,0.08)", color: "#fff", fontSize: 11 }}>Data Pipeline</span>
          </div>

          <div style={{ display: "grid", gap: 12 }}>
            {smartScoreSignals.map((signal) => (
              <div key={signal} style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
                <span style={{ color: "#d4af37", fontWeight: 800 }}>•</span>
                <div style={{ color: "var(--color-text-secondary)", lineHeight: 1.6, fontSize: 13.5 }}>{signal}</div>
              </div>
            ))}
          </div>
        </section>

        <section style={card}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
            <div>
              <div className="eyebrow">Stochastic modeling</div>
              <h2 className="wc-section-title" style={{ margin: 0, fontSize: 20 }}>Match Variance & Randomness</h2>
            </div>
            <span className="wc-badge wc-badge-gold" style={{ fontSize: 11 }}>Probability</span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 14, justifyContent: "center", height: "100%" }}>
            <div style={{ color: "var(--color-text-secondary)", lineHeight: 1.7, fontSize: 13.5, margin: 0 }}>
              Football simulations are intentionally not deterministic. While the underlying statistics form a baseline, the match engine introduces random sampling (variance) to reflect real-world upsets.
            </div>
            <div style={{ color: "rgba(255,255,255,0.45)", fontSize: 12, lineHeight: 1.6, borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: 12 }}>
              A heavy favorite may lose a single simulation due to bad variance, but running multiple iterations will showcase their statistical likelihood of victory.
            </div>
          </div>
        </section>
      </div>

    </div>
  );
}