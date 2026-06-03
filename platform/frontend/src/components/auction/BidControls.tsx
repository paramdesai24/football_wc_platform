import { useEffect, useState } from "react";
import { useAuctionStore } from "@/store/auctionStore";

interface BidControlsProps {
  currentBid: number;
  myBudget: number;
  currentBidderId: string | null;
  myUserId: string | null;
  onBid: (amount: number) => void;
}

export function BidControls({ currentBid, myBudget, currentBidderId, myUserId, onBid }: BidControlsProps) {
  const [bidAmount, setBidAmount] = useState(String(Math.max(currentBid + 50, 50)));
  const [pressing, setPressing] = useState(false);
  const [success, setSuccess] = useState(false);
  const currentPlayer = useAuctionStore((state) => state.currentPlayer);
  const bidPending = useAuctionStore((state) => state.bidPending);
  const basePrice = Number(currentPlayer?.base_price ?? 0);

  useEffect(() => {
    if (currentBid <= 0 && basePrice > 0) {
      setBidAmount(String(basePrice));
      return;
    }
    setBidAmount(String(Math.max(currentBid + 50, 50)));
  }, [currentBid, basePrice]);

  // Clear pending state when the bid is reflected in the store (bid_placed arrived)
  useEffect(() => {
    if (bidPending && currentBid > 0) {
      useAuctionStore.getState().setBidPending(false);
    }
  }, [currentBid, bidPending]);

  const status = useAuctionStore((state) => state.status);
  const isPaused = status === "paused";

  const parsedBid = Number(bidAmount);
  const bidDisabled = Number.isNaN(parsedBid) || parsedBid <= currentBid || parsedBid > myBudget;
  const isCurrentHighBidder = Boolean(currentBidderId && myUserId && currentBidderId === myUserId && currentBid > 0);
  const buttonDisabled = bidDisabled || isCurrentHighBidder || bidPending || isPaused;

  const handleBid = () => {
    if (buttonDisabled) return;
    setPressing(true);
    setTimeout(() => setPressing(false), 200);
    onBid(parsedBid);
    setSuccess(true);
    setTimeout(() => setSuccess(false), 400);
  };

  const buttonLabel = bidPending
    ? "Placing…"
    : isPaused
      ? "Paused"
      : isCurrentHighBidder
        ? "Highest bidder"
        : "BID";

  return (
    <div className="wc-card" style={{ padding: 18, display: "grid", gap: 14 }}>
      <div style={{ display: "grid", gap: 8 }}>
        <label style={{ fontSize: 11, fontWeight: 500, letterSpacing: "0.08em", textTransform: "uppercase", color: "rgba(255,255,255,0.38)", lineHeight: 1 }}>Bid amount</label>
        <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
          <input
            id="bid-amount-input"
            type="number"
            min={currentBid + 1}
            max={myBudget}
            value={bidAmount}
            disabled={isPaused}
            onChange={(event) => setBidAmount(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                handleBid();
              }
            }}
            style={{
              flex: 1,
              minWidth: 180,
              height: 46,
              borderRadius: 14,
              border: "1px solid rgba(255,255,255,0.12)",
              background: "rgba(255,255,255,0.04)",
              color: "#fff",
              padding: "0 14px",
              fontSize: 16,
              outline: "none",
            }}
          />
          <button
            type="button"
            onClick={handleBid}
            disabled={buttonDisabled}
            className={`${pressing ? "btn-press" : ""} ${success ? "bid-success" : ""}`}
            style={{
              height: 46,
              padding: "0 18px",
              borderRadius: 14,
              border: "none",
              opacity: isCurrentHighBidder ? 0.4 : 1,
              cursor: buttonDisabled ? "not-allowed" : "pointer",
              background: bidPending
                ? "linear-gradient(135deg, #b8941e, #d4af37)"
                : buttonDisabled
                  ? "rgba(255,255,255,0.12)"
                  : "linear-gradient(135deg, #d4af37, #f7d774)",
              color: buttonDisabled && !bidPending ? "rgba(255,255,255,0.55)" : "#08101f",
              fontWeight: 800,
              letterSpacing: "0.08em",
              transition: "all 0.15s ease",
              animation: bidPending ? "bidPulse 0.8s ease-in-out infinite" : "none",
            }}
          >
            {buttonLabel}
          </button>
        </div>
        <div style={{ color: "var(--color-text-muted)", fontSize: 12 }}>
          {(!currentBid || currentBid <= 0)
            ? `Opening bid: ${basePrice.toLocaleString()} coins (base price) · Your budget: ${myBudget.toLocaleString()} coins`
            : `Current bid: ${currentBid.toLocaleString()} coins · Minimum next: ${(currentBid + 10).toLocaleString()} coins · Your budget: ${myBudget.toLocaleString()} coins`}
        </div>
      </div>

      <div style={{ display: "flex", flexWrap: "wrap", gap: 14, paddingTop: 12, borderTop: "1px solid rgba(255, 255, 255, 0.08)", marginTop: 4 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11, color: "rgba(255,255,255,0.4)" }}>
          <kbd style={{ background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.15)", borderRadius: 4, padding: "2px 6px", fontFamily: "var(--font-mono)", fontSize: 10, color: "#fff" }}>B</kbd>
          <span>Focus Bid</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11, color: "rgba(255,255,255,0.4)" }}>
          <kbd style={{ background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.15)", borderRadius: 4, padding: "2px 6px", fontFamily: "var(--font-mono)", fontSize: 10, color: "#fff" }}>Space</kbd>
          <span>Quick +50</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11, color: "rgba(255,255,255,0.4)" }}>
          <kbd style={{ background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.15)", borderRadius: 4, padding: "2px 6px", fontFamily: "var(--font-mono)", fontSize: 10, color: "#fff" }}>Enter</kbd>
          <span>Submit Bid</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11, color: "rgba(255,255,255,0.4)" }}>
          <kbd style={{ background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.15)", borderRadius: 4, padding: "2px 6px", fontFamily: "var(--font-mono)", fontSize: 10, color: "#fff" }}>Esc</kbd>
          <span>Cancel</span>
        </div>
      </div>

      <style>{`
        @keyframes bidPulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.85; transform: scale(0.98); }
        }
      `}</style>
    </div>
  );
}