import { useCallback, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import useWebSocket, { ReadyState } from 'react-use-websocket'
import { useAuctionStore } from "@/store/auctionStore";
import { WS_BASE } from "@/services/api";
import { toast } from "@/store/toastStore";

export function useAuctionSocket(leagueId: string, userId: string, username: string) {
  const navigate = useNavigate();
  const resolvedUseWebSocket = typeof useWebSocket === "function"
    ? useWebSocket
    : (useWebSocket as unknown as { default?: typeof useWebSocket }).default ?? useWebSocket;
  const OPEN_STATE = typeof ReadyState?.OPEN === "number" ? ReadyState.OPEN : 1;

  const setConnectionStatus = useAuctionStore((s) => s.setConnectionStatus);
  const addMessage = useAuctionStore((s) => s.addMessage);
  const setTimer = useAuctionStore((s) => s.setTimer);
  const setStatus = useAuctionStore((s) => s.setStatus);
  const setMaxTimer = useAuctionStore((s) => s.setMaxTimer);
  const setCurrentPlayer = useAuctionStore((s) => s.setCurrentPlayer);
  const setHighBid = useAuctionStore((s) => s.setHighBid);
  const setUpcoming = useAuctionStore((s) => s.setUpcoming);
  const applyServerState = useAuctionStore((s) => s.applyServerState);

  // If userId is empty, the WebSocket won't connect.
  const wsUrl = useMemo(
    () => (leagueId && userId && username
      ? `${WS_BASE.replace(/\/$/, '')}/ws/auction/${leagueId}?user_id=${encodeURIComponent(userId)}&username=${encodeURIComponent(username)}`
      : null),
    [leagueId, userId, username],
  );

  const handleOpen = useCallback(() => {
    setConnectionStatus('connected');
    addMessage("🟢 Connected to auction room");
  }, [addMessage, setConnectionStatus]);

  const handleClose = useCallback(() => {
    setConnectionStatus('reconnecting');
    addMessage("🔌 Connection closed, retrying...");
  }, [addMessage, setConnectionStatus]);

  const handleError = useCallback(() => {
    setConnectionStatus('disconnected');
  }, [setConnectionStatus]);

  const handleMessage = useCallback((event: MessageEvent<string>) => {
    const { type, payload } = JSON.parse(event.data as string) as { type: string; payload: any };

    if (type === 'timer_tick') {
      setTimer(payload.seconds_left)
    }

    if (type === "auction_started") {
      setStatus("active");
      addMessage(`🏁 Auction started — ${payload.total_players} players in the pool`);
    }

    if (type === "room_state") {
      const existingUsers = useAuctionStore.getState().users ?? {};
      const users = Object.fromEntries(
        Object.entries(payload.users ?? {}).map(([userId, user]) => [
          userId,
          {
            ...user,
            squad: (user as any)?.squad ?? (existingUsers[userId] as any)?.squad ?? [],
            squad_details: (user as any)?.squad_details ?? (existingUsers[userId] as any)?.squad_details ?? [],
          },
        ]),
      );
      applyServerState({ ...payload, users });
      if (payload.current_player) {
        const hasBid = (payload.current_high_bid ?? 0) > 0;
        setMaxTimer(hasBid ? 30 : 60);
      }
    }

    if (type === "player_nominated") {
      setStatus("active");
      setMaxTimer(60);
      setCurrentPlayer(payload.player);
      setHighBid(0, null);
      setUpcoming(payload.upcoming ?? []);
      setTimer(payload.timer);
      addMessage(`🎯 Now bidding: ${payload.player.name} · Base: ${payload.player.base_price?.toLocaleString()} coins`);
    }

    if (type === "bid_rejected") {
      addMessage(`⚠️ Bid rejected: ${payload?.reason ?? "Unknown reason"}`);
      toast.warning(payload?.reason ?? "Unknown reason");
      useAuctionStore.getState().setBidPending(false);
    }

    if (type === "bid_placed") {
      setMaxTimer(30);
      setHighBid(payload.amount, payload.user_id);
      setTimer(payload.timer_reset_to);
      addMessage(`💰 ${payload.username} bid ${payload.amount.toLocaleString()} coins`);
      useAuctionStore.getState().setBidPending(false);
    }

    if (type === "bid_ack") {
      // Immediate acknowledgment from server — bid accepted, broadcast coming next
      useAuctionStore.getState().setBidPending(false);
    }

    if (type === "player_sold") {
      addMessage(`✅ ${payload.player.name} → ${payload.winner} for ${payload.price} coins`);
      toast.success(`${payload.player?.name} → ${payload.winner} for ${payload.price} coins`);
      setCurrentPlayer(null);
    }

    if (type === "player_skipped") {
      addMessage(`⏭️ ${payload.player?.name ?? 'Player'} skipped by ${payload.skipped_by}`);
      setCurrentPlayer(null);
    }

    if (type === "user_joined") {
      addMessage(`👋 ${payload.username} joined`);
    }

    if (type === "user_left") {
      addMessage(`👋 ${payload.username ?? payload.user_id} left`);
    }

    if (type === "auction_complete") {
      setStatus("complete");
      addMessage("🏁 Auction complete!");
    }

    if (type === "auction_paused") {
      setStatus("paused");
      setTimer(payload.seconds_left);
      addMessage(`⏸️ ${payload.message}`);
      toast.warning("Auction paused by host");
    }

    if (type === "auction_resumed") {
      setStatus("bidding");
      setTimer(payload.seconds_left);
      addMessage(`▶️ ${payload.message}`);
      toast.success("Auction resumed!");
    }

    if (type === "error") {
      addMessage(`❌ ${payload.message}`);
      toast.error(payload.message);
    }
  }, [addMessage, applyServerState, setCurrentPlayer, setHighBid, setMaxTimer, setStatus, setTimer, setUpcoming]);

  const { sendJsonMessage, readyState } = resolvedUseWebSocket(wsUrl, {
    shouldReconnect: () => true,
    reconnectInterval: 3000,
    reconnectAttempts: 20,
    onOpen: handleOpen,
    onClose: handleClose,
    onError: handleError,
    onMessage: handleMessage,
  });

  const placeBid = (amount: number) => {
    useAuctionStore.getState().setBidPending(true);
    sendJsonMessage({ type: "place_bid", payload: { amount } });
  };
  const startAuction = () => {
    addMessage("🎬 Auction start requested");
    sendJsonMessage({ type: "start_auction", payload: {} });
  };
  const confirmSale = () => {
    addMessage("✅ Confirm sale requested");
    sendJsonMessage({ type: "confirm_sale", payload: {} });
  };
  const skipPlayer = () => {
    addMessage("⏭️ Skip requested");
    sendJsonMessage({ type: "skip_player", payload: {} });
  };
  const stopAuction = () => {
    addMessage("🛑 Stop auction requested");
    sendJsonMessage({ type: "stop_auction", payload: {} });
  };
  const pauseAuction = () => {
    addMessage("⏸️ Pause auction requested");
    sendJsonMessage({ type: "pause_auction", payload: {} });
  };
  const resumeAuction = () => {
    addMessage("▶️ Resume auction requested");
    sendJsonMessage({ type: "resume_auction", payload: {} });
  };
  const leaveAuction = () => {
    navigate('/auction');
  };
  const isConnected = readyState === OPEN_STATE || readyState === 1;

  return { placeBid, startAuction, stopAuction, skipPlayer, confirmSale, leaveAuction, isConnected, pauseAuction, resumeAuction };
}