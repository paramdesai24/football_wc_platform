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
  const currentPlayer = useAuctionStore((state) => state.currentPlayer);

  useEffect(() => {
    setBidAmount(String(Math.max(currentBid + 50, 50)));
  }, [currentBid]);

  const parsedBid = Number(bidAmount);
  const bidDisabled = Number.isNaN(parsedBid) || parsedBid <= currentBid || parsedBid > myBudget;
  const isCurrentHighBidder = Boolean(currentBidderId && myUserId && currentBidderId === myUserId && currentBid > 0);
  const buttonDisabled = bidDisabled || isCurrentHighBidder;

  return (
    <div className="wc-card" style={{ padding: 18, display: "grid", gap: 14 }}>
      <div style={{ display: "grid", gap: 8 }}>
        <label style={{ color: "var(--color-text-muted)", fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase" }}>Bid amount</label>
        <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
          <input
            type="number"
            min={currentBid + 1}
            max={myBudget}
            value={bidAmount}
            onChange={(event) => setBidAmount(event.target.value)}
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
            onClick={() => onBid(parsedBid)}
            disabled={buttonDisabled}
            style={{
              height: 46,
              padding: "0 18px",
              borderRadius: 14,
              border: "none",
              opacity: isCurrentHighBidder ? 0.4 : 1,
              cursor: buttonDisabled ? "not-allowed" : "pointer",
              background: buttonDisabled ? "rgba(255,255,255,0.12)" : "linear-gradient(135deg, #d4af37, #f7d774)",
              color: buttonDisabled ? "rgba(255,255,255,0.55)" : "#08101f",
              fontWeight: 800,
              letterSpacing: "0.08em",
            }}
          >
            {isCurrentHighBidder ? "Highest bidder" : "BID"}
          </button>
        </div>
        <div style={{ color: "var(--color-text-muted)", fontSize: 12 }}>
          {(!currentBid || currentBid <= 0)
            ? `No bids yet · Starting price: ${(currentPlayer?.base_price ?? 0).toLocaleString()} coins`
            : `Current bid: ${currentBid.toLocaleString()} coins`} · Your budget: {myBudget.toLocaleString()} coins
        </div>
      </div>
    </div>
  );
}