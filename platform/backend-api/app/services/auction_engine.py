import asyncio
from random import shuffle
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


INITIAL_BID_TIMEOUT = 60
BETWEEN_BID_TIMEOUT = 30


def build_nomination_queue(players: list[dict]) -> list[dict]:
    """
    Group players into tier+position buckets, shuffle each,
    then interleave so auction cycles through all tiers and positions.
    """
    TIER_ORDER = ["Elite", "World Class", "Quality", "Rotation", "Depth"]
    POS_ORDER = ["GK", "DEF", "MID", "FWD"]

    buckets: dict[str, dict[str, list]] = {
        tier: {pos: [] for pos in POS_ORDER}
        for tier in TIER_ORDER
    }

    for player in players:
        tier = player.get("tier", "Depth")
        pos = player.get("position", "MID")
        if tier in buckets and pos in buckets[tier]:
            buckets[tier][pos].append(player)

    for tier in TIER_ORDER:
        for pos in POS_ORDER:
            shuffle(buckets[tier][pos])

    queue = []
    for tier in TIER_ORDER:
        for pos in POS_ORDER:
            queue.extend(buckets[tier][pos])

    return queue


@dataclass
class RoomUser:
    user_id: str
    username: str
    budget_left: int
    squad: List[str] = field(default_factory=list)


@dataclass
class AuctionRoom:
    league_id: str
    users: Dict[str, RoomUser] = field(default_factory=dict)
    status: str = "waiting"
    current_player_id: Optional[str] = None
    current_player: Optional[dict] = None
    current_high_bid: int = 0
    current_bidder_id: Optional[str] = None
    timer_task: Optional[asyncio.Task] = field(default=None)
    timer_seconds: int = 30
    nomination_queue_data: List[dict] = field(default_factory=list)
    queue_index: int = 0
    has_received_bid: bool = False
    sold_players: List[str] = field(default_factory=list)
    connections: Dict[str, Any] = field(default_factory=dict)

    def to_state(self) -> dict:
        return {
            "league_id": self.league_id,
            "status": self.status,
            "current_player": self.current_player,
            "current_high_bid": self.current_high_bid,
            "current_bidder_id": self.current_bidder_id,
            "users": {
                uid: {
                    "username": user.username,
                    "budget_left": user.budget_left,
                    "squad_size": len(user.squad),
                }
                for uid, user in self.users.items()
            },
            "sold_count": len(self.sold_players),
            "queue_index": self.queue_index,
            "queue_size": len(self.nomination_queue_data),
        }


ACTIVE_ROOMS: Dict[str, AuctionRoom] = {}


def get_or_create_room(league_id: str) -> AuctionRoom:
    if league_id not in ACTIVE_ROOMS:
        ACTIVE_ROOMS[league_id] = AuctionRoom(league_id=league_id)
    return ACTIVE_ROOMS[league_id]