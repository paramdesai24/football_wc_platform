import { FlagImg } from "@/components/FlagImg";
import type { AuctionPlayer } from "@/store/auctionStore";
import { SpringNumber } from "@/components/ui/SpringNumber";

interface PlayerCardProps {
  player: AuctionPlayer;
  currentBid: number;
  isOnBlock?: boolean;
}

export function PlayerCard({ player, currentBid }: PlayerCardProps) {
  if (!player) return (
    <div className="wc-card" style={{ padding: 30, textAlign: "center", color: "var(--color-text-secondary)" }}>
      <div style={{ fontSize: 32, marginBottom: 8 }}>⚽</div>
      Waiting for next nomination...
    </div>
  )

  const hasNoBids = !currentBid || currentBid <= 0

  return (
    <div className="wc-card" style={{ padding: 24, display: "grid", gap: 20, border: "1px solid rgba(212,175,55,0.4)", boxShadow: "0 0 25px rgba(212,175,55,0.15), 0 24px 60px rgba(0,0,0,0.4)" }}>
      {/* Top bar: tier + position + ON THE BLOCK */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div style={{ display: "flex", gap: 8 }}>
          <span style={{ padding: "4px 8px", borderRadius: 6, background: "rgba(212,175,55,0.15)", color: "#d4af37", fontSize: 10, fontWeight: 700, letterSpacing: "0.05em" }}>
            {player.tier?.toUpperCase()}
          </span>
          <span style={{ padding: "4px 8px", borderRadius: 6, background: "rgba(255,255,255,0.06)", color: "rgba(255,255,255,0.7)", fontSize: 10, fontWeight: 700 }}>
            {player.position}
          </span>
        </div>
        <span style={{ color: "#d4af37", fontSize: 10, fontWeight: 800, letterSpacing: "0.1em" }}>
          ON THE BLOCK
        </span>
      </div>

      {/* Player photo — large, centered */}
      <div style={{ display: "flex", justifyContent: "center", margin: "10px 0" }}>
        {player.image_url ? (
          <img
            src={player.image_url}
            alt={player.name}
            style={{ width: 140, height: 140, borderRadius: 16, objectFit: "cover", border: "2px solid rgba(255,255,255,0.1)", boxShadow: "0 8px 20px rgba(0,0,0,0.5)" }}
          />
        ) : (
          <div style={{ width: 140, height: 140, borderRadius: 16, background: "rgba(255,255,255,0.04)", border: "2px solid rgba(255,255,255,0.1)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 48 }}>
            ⚽
          </div>
        )}
      </div>

      {/* Name + flag + club */}
      <div style={{ textAlign: "center" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8, marginBottom: 4 }}>
          <FlagImg code={player.flag_code} size={20} />
          <h2 style={{ fontSize: "1.75rem", fontWeight: 800, color: "#fff", margin: 0, fontFamily: "var(--font-display)", letterSpacing: "-0.02em" }}>
            {player.name}
          </h2>
        </div>
        <div style={{ fontSize: 13, color: "rgba(255,255,255,0.5)", fontWeight: 500 }}>
          {player.club}
        </div>
      </div>

      {/* Stats — 2 column grid */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
        {[
          { label: 'MARKET VALUE', value: player.market_value >= 1_000_000 ? `€${(player.market_value/1_000_000).toFixed(0)}M` : `€${(player.market_value/1_000).toFixed(0)}K` },
          { label: 'BASE PRICE',   value: `${player.base_price?.toLocaleString()} coins` },
          { label: 'GOALS',        value: player.goals_2526 ?? 0 },
          { label: 'ASSISTS',      value: player.assists_2526 ?? 0 },
          { label: 'MINUTES',      value: `${(player.minutes_2526 ?? 0).toLocaleString()}'` },
          { label: 'FORM',         value: player.form_score ? player.form_score.toFixed(1) : '—' },
        ].map(s => (
          <div key={s.label} style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.05)", borderRadius: 10, padding: "8px 12px" }}>
            <div style={{ fontSize: 9, color: "rgba(255,255,255,0.4)", fontWeight: 600, letterSpacing: "0.05em", marginBottom: 2 }}>
              {s.label}
            </div>
            <div style={{ fontSize: 13, color: "#fff", fontWeight: 700, fontFamily: "var(--font-ui)" }}>
              {s.value}
            </div>
          </div>
        ))}
      </div>

      {/* Current bid — hero display */}
      <div style={{ background: "rgba(212,175,55,0.08)", border: "1px solid rgba(212,175,55,0.2)", borderRadius: 12, padding: "12px", textAlign: "center" }}>
        <div style={{ fontSize: 10, color: "rgba(212,175,55,0.6)", fontWeight: 800, letterSpacing: "0.08em", marginBottom: 4 }}>
          CURRENT BID
        </div>
        <div style={{ fontSize: "1.75rem", color: "#d4af37", fontWeight: 800, fontFamily: "var(--font-display)" }}>
          {hasNoBids ? '—' : (
            <SpringNumber
              value={currentBid}
              style={{ fontFamily: "var(--font-display)", fontSize: "1.75rem", fontWeight: 800, color: "#d4af37" }}
              formatter={n => Math.round(n).toLocaleString() + " coins"}
            />
          )}
        </div>
      </div>
    </div>
  )
}