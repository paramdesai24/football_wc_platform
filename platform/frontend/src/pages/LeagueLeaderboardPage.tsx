import { useParams } from "react-router-dom";

export default function LeagueLeaderboardPage() {
  const { id = "" } = useParams();

  return (
    <div className="page-container">
      <section className="wc-card" style={{ padding: 24, display: "grid", gap: 12 }}>
        <div style={{ color: "var(--color-accent)", fontSize: 11, letterSpacing: "0.16em", textTransform: "uppercase", fontWeight: 700 }}>Leaderboard</div>
        <h1 style={{ margin: 0, fontFamily: "var(--font-display)", fontSize: "clamp(2rem, 5vw, 3rem)" }}>League {id || "details"}</h1>
        <p style={{ margin: 0, color: "var(--color-text-secondary)" }}>Leaderboard data can be rendered here from the backend API once league points are fetched.</p>
      </section>
    </div>
  );
}