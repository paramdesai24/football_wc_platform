import useWebSocket, { ReadyState } from 'react-use-websocket'
import { useAuctionStore } from "@/store/auctionStore";
import { WS_BASE } from "@/services/api";

export function useAuctionSocket(leagueId: string, userId: string, username: string) {
  const store = useAuctionStore();
  const resolvedUseWebSocket = typeof useWebSocket === "function"
    ? useWebSocket
    : (useWebSocket as unknown as { default?: typeof useWebSocket }).default ?? useWebSocket;
  const OPEN_STATE = typeof ReadyState?.OPEN === "number" ? ReadyState.OPEN : 1;

  const wsUrl = leagueId && userId && username
    ? `${WS_BASE.replace(/\/$/, '')}/ws/auction/${leagueId}?user_id=${encodeURIComponent(userId)}&username=${encodeURIComponent(username)}`
    : null;

  const { sendJsonMessage, readyState } = resolvedUseWebSocket(wsUrl, {
    shouldReconnect: () => true,
    reconnectInterval: 3000,
    onOpen: () => {
      store.addMessage("🟢 Connected to auction room");
    },
    onClose: () => {
      store.addMessage("🔌 Connection closed, retrying...");
    },
    onMessage: (event: MessageEvent<string>) => {
      const { type, payload } = JSON.parse(event.data as string) as { type: string; payload: any };

      if (type === 'timer_tick') {
        store.setTimer(payload.seconds_left)
      }

      if (type === "auction_started") {
        store.setStatus("active");
        store.addMessage(`🏁 Auction started — ${payload.total_players} players in the pool`);
      }

      if (type === "room_state") {
        const existingUsers = useAuctionStore.getState().users ?? {};
        const users = Object.fromEntries(
          Object.entries(payload.users ?? {}).map(([userId, user]) => [
            userId,
            {
              ...user,
              squad: (user as any)?.squad ?? (existingUsers[userId] as any)?.squad ?? [],
            },
          ]),
        );
        store.applyServerState({ ...payload, users });
      }

      if (type === "player_nominated") {
        store.setStatus("active");
        store.setMaxTimer(60);
        store.setCurrentPlayer(payload.player);
        store.setHighBid(0, null);
        store.setUpcoming(payload.upcoming ?? []);
        store.setTimer(payload.timer);
        store.addMessage(`🎯 Now bidding: ${payload.player.name} · Base: ${payload.player.base_price?.toLocaleString()} coins`);
      }

      if (type === "bid_rejected") {
        store.addMessage(`⚠️ Bid rejected: ${payload?.reason ?? "Unknown reason"}`);
      }

      if (type === "bid_placed") {
        store.setMaxTimer(30);
        store.setHighBid(payload.amount, payload.user_id);
        store.setTimer(payload.timer_reset_to);
        store.addMessage(`💰 ${payload.username} bid ${payload.amount.toLocaleString()} coins`);
      }

      if (type === "player_sold") {
        store.addMessage(`✅ ${payload.player.name} → ${payload.winner} for ${payload.price} coins`);
        store.setCurrentPlayer(null);
      }

      if (type === "user_joined") {
        store.addMessage(`👋 ${payload.username} joined`);
      }

      if (type === "auction_complete") {
        store.addMessage("🏁 Auction complete!");
      }

      if (type === "error") {
        store.addMessage(`❌ ${payload.message}`);
      }
    },
  });

  const placeBid = (amount: number) => sendJsonMessage({ type: "place_bid", payload: { amount } });
  const startAuction = () => {
    store.addMessage("🎬 Auction start requested");
    sendJsonMessage({ type: "start_auction", payload: {} });
  };
  const isConnected = readyState === OPEN_STATE || readyState === 1;

  return { placeBid, startAuction, isConnected };
}