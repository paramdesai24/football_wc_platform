import { Link, useParams } from "react-router-dom";

export default function LeaguePage() {
  const { id = "" } = useParams();

  return (
    <div className="page-container" style={{ display: "grid", gap: 16 }}>
      <section className="wc-card" style={{ padding: 24, display: "grid", gap: 12 }}>
        <div style={{ color: "var(--color-accent)", fontSize: 11, letterSpacing: "0.16em", textTransform: "uppercase", fontWeight: 700 }}>League hub</div>
        <h1 style={{ margin: 0, fontFamily: "var(--font-display)", fontSize: "clamp(2rem, 5vw, 3rem)" }}>League {id || "details"}</h1>
        <p style={{ margin: 0, color: "var(--color-text-secondary)", maxWidth: 720 }}>View your squad, compare budgets, and jump into the live auction board from here.</p>
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
          <ActionLink to={`/auction/room/${id || "demo-league"}`}>Enter room</ActionLink>
          <ActionLink to={`/league/${id || "demo-league"}/leaderboard`}>Leaderboard</ActionLink>
          <ActionLink to={`/league/${id || "demo-league"}/squad/demo-user`}>My squad</ActionLink>
        </div>
      </section>
    </div>
  );
}

function ActionLink({ to, children }: { to: string; children: React.ReactNode }) {
  return (
    <Link to={to} style={{ textDecoration: "none" }}>
      <span style={{ display: "inline-flex", alignItems: "center", justifyContent: "center", minHeight: 44, padding: "0 18px", borderRadius: 14, border: "1px solid rgba(255,255,255,0.12)", color: "#fff", fontWeight: 700 }}>{children}</span>
    </Link>
  );
}