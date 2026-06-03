import { FlagImg } from "@/components/FlagImg";
import type { AuctionPlayer } from "@/store/auctionStore";
import { SpringNumber } from "@/components/ui/SpringNumber";

interface PlayerCardProps {
  player: AuctionPlayer;
  currentBid: number;
  isOnBlock: boolean;
}

const money = new Intl.NumberFormat("en-US");

function formatMinutes(value: number) {
  return `${Math.round(value).toLocaleString()}'`;
}

function formatMarketValue(value: number) {
  if (value >= 1_000_000) {
    return `€${(value / 1_000_000).toFixed(0)}M`;
  }
  return `€${(value / 1_000).toFixed(0)}K`;
}

export function PlayerCard({ player, currentBid, isOnBlock }: PlayerCardProps) {
  const hasBid = currentBid > 0;

  return (
    <div className="wc-card" style={{ padding: 20, display: "grid", gap: 16, border: isOnBlock ? "1px solid rgba(212,175,55,0.55)" : "1px solid rgba(255,255,255,0.08)", boxShadow: isOnBlock ? "0 0 0 1px rgba(212,175,55,0.18), 0 24px 60px rgba(0,0,0,0.28)" : "none" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <span style={{ padding: "5px 10px", borderRadius: 999, background: "rgba(212,175,55,0.14)", color: "var(--color-accent)", fontSize: 11, fontWeight: 700, letterSpacing: "0.12em", textTransform: "uppercase" }}>{player.tier}</span>
          <span style={{ padding: "5px 10px", borderRadius: 999, background: "rgba(255,255,255,0.08)", color: "var(--color-text-secondary)", fontSize: 11, fontWeight: 700, textTransform: "uppercase" }}>{player.position}</span>
        </div>
        {isOnBlock && <span style={{ color: "var(--color-accent)", fontSize: 12, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase" }}>On the block</span>}
      </div>

      <div className="player-card-inner">
        <div style={{ position: "relative", width: 110, height: 110, borderRadius: 20, overflow: "hidden", background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.08)" }}>
          <img
            src={player.image_url}
            alt={player.name}
            loading="lazy"
            style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }}
            onError={(event) => {
              (event.currentTarget as HTMLImageElement).style.opacity = "0";
            }}
          />
        </div>

        <div style={{ display: "grid", gap: 10, minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
            <FlagImg code={player.flag_code} size={24} />
            <div style={{ minWidth: 0 }}>
              <h2 style={{ margin: 0, fontFamily: "var(--font-display)", fontSize: "2rem", letterSpacing: "-0.03em", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }} title={player.name}>{player.name}</h2>
              <div style={{ color: "var(--color-text-secondary)", fontSize: 14, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }} title={player.club}>{player.club}</div>
            </div>
          </div>

          <div className="player-card-metrics">
            <Metric label="Market value" value={formatMarketValue(player.market_value)} />
            <div style={{
              padding: "10px 12px",
              borderRadius: 16,
              background: "rgba(212,175,55,0.12)",
              border: "1px solid rgba(212,175,55,0.3)",
              minWidth: 0,
              overflow: "hidden"
            }}>
              <div style={{ fontSize: 11, fontWeight: 500, letterSpacing: "0.08em", textTransform: "uppercase", color: "rgba(255,255,255,0.38)", lineHeight: 1, marginBottom: 4 }}>Current bid</div>
              <div style={{ color: "#fff", lineHeight: 1.1 }}>
                {hasBid ? (
                  <SpringNumber value={currentBid} style={{ fontFamily: "var(--font-display)", fontSize: "clamp(28px,4vw,48px)", fontWeight: 800, letterSpacing: "-0.01em", lineHeight: 1, color: "#d4af37" }} formatter={n => Math.round(n).toLocaleString() + " coins"} />
                ) : "—"}
              </div>
            </div>
            <Metric label="Goals" value={player.goals_2526} />
            <Metric label="Assists" value={player.assists_2526} />
          </div>
        </div>
      </div>

      <div className="player-card-ministats">
        <MiniStat label="Minutes" value={formatMinutes(player.minutes_2526)} />
        <MiniStat label="Form" value={player.form_score.toFixed(1)} />
        <MiniStat label="Base price" value={`${money.format(player.base_price)} coins`} />
      </div>
    </div>
  );
}

function Metric({ label, value, highlight, valueClassName }: { label: string; value: string | number; highlight?: boolean; valueClassName?: string }) {
  return (
    <div style={{
      padding: "10px 12px",
      borderRadius: 16,
      background: highlight ? "rgba(212,175,55,0.12)" : "rgba(255,255,255,0.04)",
      border: highlight ? "1px solid rgba(212,175,55,0.3)" : "1px solid rgba(255,255,255,0.06)",
      minWidth: 0,
      overflow: "hidden"
    }}>
      <div style={{ fontSize: 11, fontWeight: 500, letterSpacing: "0.08em", textTransform: "uppercase", color: "rgba(255,255,255,0.38)", lineHeight: 1, marginBottom: 4 }} title={label}>
        {label}
      </div>
      <div
        className={valueClassName}
        style={{
          color: "#fff",
          fontFamily: valueClassName ? undefined : "var(--font-display)",
          fontSize: valueClassName ? undefined : "clamp(1.15rem, 2vw, 1.45rem)",
          fontWeight: valueClassName ? undefined : 700,
          lineHeight: 1.1,
          whiteSpace: "nowrap",
          overflow: "hidden",
          textOverflow: "ellipsis"
        }}
        title={String(value)}
      >
        {value}
      </div>
    </div>
  );
}

function MiniStat({ label, value }: { label: string; value: string }) {
  return (
    <div style={{
      padding: "10px 12px",
      borderRadius: 16,
      background: "rgba(255,255,255,0.04)",
      border: "1px solid rgba(255,255,255,0.06)",
      minWidth: 0,
      overflow: "hidden"
    }}>
      <div style={{
        color: "var(--color-text-muted)",
        fontSize: 10,
        letterSpacing: "0.08em",
        textTransform: "uppercase",
        marginBottom: 4,
        whiteSpace: "nowrap",
        overflow: "hidden",
        textOverflow: "ellipsis"
      }} title={label}>
        {label}
      </div>
      <div style={{
        color: "#fff",
        fontFamily: "var(--font-ui)",
        fontSize: 13,
        fontWeight: 700,
        whiteSpace: "nowrap",
        overflow: "hidden",
        textOverflow: "ellipsis"
      }} title={value}>
        {value}
      </div>
    </div>
  );
}