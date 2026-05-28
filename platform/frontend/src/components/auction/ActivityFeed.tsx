interface ActivityFeedProps {
  messages: string[];
}

export function ActivityFeed({ messages }: ActivityFeedProps) {
  return (
    <div className="wc-card" style={{ padding: 18, display: "grid", gap: 12, minHeight: 0 }}>
      <div style={{ color: "var(--color-text-secondary)", fontSize: 11, letterSpacing: "0.14em", textTransform: "uppercase" }}>Activity</div>
      <div style={{ display: "grid", gap: 8, maxHeight: 290, overflowY: "auto", paddingRight: 4 }}>
        {messages.length === 0 ? (
          <div style={{ color: "var(--color-text-muted)", fontSize: 13 }}>Waiting for auction events.</div>
        ) : (
          messages.map((message, index) => (
            <div key={`${message}-${index}`} style={{ padding: 12, borderRadius: 14, background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.06)", color: "#fff", fontSize: 14, lineHeight: 1.4 }}>
              {message}
            </div>
          ))
        )}
      </div>
    </div>
  );
}