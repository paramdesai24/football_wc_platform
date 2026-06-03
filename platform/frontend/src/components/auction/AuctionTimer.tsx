interface AuctionTimerProps {
  seconds:     number;
  maxSeconds?: number;
  isActive?:   boolean;
  isPaused?:   boolean;
}

export function AuctionTimer({ seconds, maxSeconds = 60, isActive = true, isPaused = false }: AuctionTimerProps) {
  if (!isActive) return null;

  const progress = Math.max(0, Math.min(100, (seconds / maxSeconds) * 100));

  // Urgency thresholds
  const isCritical = seconds <= 10 && !isPaused;
  const isWarning  = seconds <= 30 && !isCritical && !isPaused;

  const ringColor = isPaused ? '#fbbf24' : isCritical ? '#ef4444' : isWarning ? '#f59e0b' : '#d4af37';
  const textColor = ringColor;

  const pulseAnim = isPaused
    ? 'none'
    : isCritical
    ? 'timerCritical 0.5s ease-in-out infinite'
    : isWarning
    ? 'timerWarning 1.2s ease-in-out infinite'
    : 'none';

  const shakeAnim = isCritical && seconds <= 5 && !isPaused
    ? 'timerShake 0.3s ease-in-out infinite'
    : 'none';

  const size   = 120;
  const stroke = 6;
  const r      = (size - stroke) / 2;
  const circ   = 2 * Math.PI * r;
  const offset = circ * (1 - progress / 100);

  return (
    <div className="wc-card" style={{ padding: 18, display: "grid", gap: 12, justifyItems: "center" }}>
      <div style={{ animation: shakeAnim }}>
        <svg
          width={size}
          height={size}
          style={{ display: 'block', animation: pulseAnim }}
          aria-label={`Timer: ${seconds} seconds remaining`}
        >
          {/* Track ring */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="rgba(5,13,26,0.98)"
            stroke="rgba(255,255,255,0.08)"
            strokeWidth={stroke}
          />
          {/* Progress ring — rotated so it drains from top */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke={ringColor}
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={circ}
            strokeDashoffset={offset}
            transform={`rotate(-90 ${size / 2} ${size / 2})`}
            style={{ transition: 'stroke-dashoffset 0.95s linear, stroke 0.4s ease' }}
          />
          {/* Center seconds */}
          <text
            x={size / 2}
            y={size / 2 - 6}
            textAnchor="middle"
            dominantBaseline="middle"
            fill={textColor}
            fontFamily="var(--font-display)"
            fontSize={28}
            fontWeight={800}
            style={{ transition: 'fill 0.4s ease' }}
          >
            {seconds}
          </text>
          {/* Label */}
          <text
            x={size / 2}
            y={size / 2 + 20}
            textAnchor="middle"
            dominantBaseline="middle"
            fill="var(--color-text-muted)"
            fontSize={10}
            fontFamily="var(--font-ui)"
            letterSpacing="0.14em"
          >
            {isPaused ? 'PAUSED' : 'SECONDS'}
          </text>
        </svg>
      </div>

      {/* Progress bar */}
      <div style={{ width: "100%", height: 8, borderRadius: 999, background: "rgba(255,255,255,0.08)", overflow: "hidden" }}>
        <div style={{
          width: `${progress}%`,
          height: "100%",
          background: isPaused ? "#fbbf24" : isCritical ? "var(--color-red)" : isWarning ? "#f59e0b" : "linear-gradient(90deg, #d4af37, #f7d774)",
          transition: "width 0.95s linear, background 0.4s ease",
        }} />
      </div>
    </div>
  );
}