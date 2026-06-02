interface AuctionTimerProps {
  seconds: number;
  maxSeconds?: number;
  isActive?: boolean;
  isPaused?: boolean;
}

export function AuctionTimer({ seconds, maxSeconds = 60, isActive = true, isPaused = false }: AuctionTimerProps) {
  if (!isActive) {
    return null;
  }

  const progress = Math.max(0, Math.min(100, (seconds / maxSeconds) * 100));
  const danger = seconds < 5 && !isPaused;
  const timerColor = isPaused ? "#fbbf24" : danger ? "var(--color-red)" : "var(--color-gold)";

  return (
    <div className="wc-card" style={{ padding: 18, display: "grid", gap: 12, justifyItems: "center" }}>
      <div
        style={{
          width: 120,
          height: 120,
          borderRadius: "50%",
          background: `conic-gradient(${timerColor} ${progress}%, rgba(255,255,255,0.08) 0)`,
          padding: 10,
        }}
      >
        <div style={{ width: "100%", height: "100%", borderRadius: "50%", background: "rgba(5,13,26,0.98)", display: "grid", placeItems: "center", border: "1px solid rgba(255,255,255,0.08)" }}>
          <div style={{ textAlign: "center" }}>
            <div style={{ color: timerColor, fontFamily: "var(--font-display)", fontSize: 34, fontWeight: 800, lineHeight: 1 }}>{seconds}</div>
            <div style={{ color: "var(--color-text-muted)", fontSize: 11, letterSpacing: "0.14em", textTransform: "uppercase", marginTop: 4 }}>
              {isPaused ? "PAUSED" : "Seconds"}
            </div>
          </div>
        </div>
      </div>
      <div style={{ width: "100%", height: 8, borderRadius: 999, background: "rgba(255,255,255,0.08)", overflow: "hidden" }}>
        <div style={{ width: `${progress}%`, height: "100%", background: isPaused ? "#fbbf24" : danger ? "var(--color-red)" : "linear-gradient(90deg, #d4af37, #f7d774)" }} />
      </div>
    </div>
  );
}