from __future__ import annotations

import asyncio
import uuid

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy import select, update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auction_models import AuctionPlayer, Bid, League, LeagueMember, Squad
from app.services.auction_engine import AuctionRoom, RoomUser, get_or_create_room


def _as_uuid(value: str):
    try:
        return uuid.UUID(value)
    except (ValueError, TypeError, AttributeError):
        return None


def _squad_player_id(entry: object) -> str:
    if isinstance(entry, dict):
        return str(entry.get("id") or "")
    return str(entry or "")


def _squad_purchase_price(entry: object) -> int:
    if isinstance(entry, dict):
        try:
            return int(entry.get("purchase_price") or 0)
        except (TypeError, ValueError):
            return 0
    return 0


def get_player_info(room: AuctionRoom, player_id: str, purchase_price: int = 0) -> dict:
    """Look up cached player info from nomination queue data."""
    for player in room.nomination_queue_data:
        if player.get("id") == player_id:
            return {
                "id": player_id,
                "name": player.get("name", player_id),
                "position": player.get("position", ""),
                "flag_code": player.get("flag_code", "un"),
                "club": player.get("club", ""),
                "purchase_price": purchase_price,
            }
    return {
        "id": player_id,
        "name": player_id,
        "position": "",
        "flag_code": "un",
        "club": "",
        "purchase_price": purchase_price,
    }


async def broadcast(room: AuctionRoom, message: dict) -> None:
    dead: list[str] = []
    for uid, ws in list(room.connections.items()):
        try:
            await ws.send_json(message)
        except Exception:
            dead.append(uid)
    for uid in dead:
        room.connections.pop(uid, None)


async def _serialize_room_state(room: AuctionRoom, db: AsyncSession) -> dict:
    state = room.to_state()
    squad_ids = {
        _squad_player_id(player_entry)
        for user in room.users.values()
        for player_entry in user.squad
        if _squad_player_id(player_entry)
    }
    position_map: dict[str, str] = {}
    if squad_ids:
        squad_result = await db.execute(
            select(AuctionPlayer.id, AuctionPlayer.position).where(AuctionPlayer.id.in_(squad_ids))
        )
        position_map = {player_id: position for player_id, position in squad_result.all()}
    state["users"] = {
        user_id: {
            **user_state,
            "squad_details": [
                get_player_info(room, player_id, _squad_purchase_price(entry))
                for entry in room.users[user_id].squad
                for player_id in [_squad_player_id(entry)]
                if player_id
            ] if user_id in room.users else [],
            "squad": [
                {
                    "id": player_id,
                    "position": position_map.get(player_id, "MID"),
                    "purchase_price": _squad_purchase_price(entry),
                }
                for entry in room.users[user_id].squad
                for player_id in [_squad_player_id(entry)]
                if player_id
            ] if user_id in room.users else [],
        }
        for user_id, user_state in state.get("users", {}).items()
    }
    return state


async def all_squads_complete(room: AuctionRoom, db: AsyncSession) -> bool:
    """
    Returns True only when every user's squad meets ALL conditions:
    1. Total players == league.squad_size
    2. GK count >= league.min_gk
    3. DEF count >= league.min_def
    4. MID count >= league.min_mid
    5. FWD count >= league.min_fwd
    """
    if not room.users:
        return False

    league_result = await db.execute(
        select(League).where(League.id == uuid.UUID(room.league_id))
    )
    league = league_result.scalar_one_or_none()
    if not league:
        return False

    squad_size = int(league.squad_size or 0)
    min_requirements = {
        "GK": int(league.min_gk or 0),
        "DEF": int(league.min_def or 0),
        "MID": int(league.min_mid or 0),
        "FWD": int(league.min_fwd or 0),
    }

    squad_ids = {
        _squad_player_id(player_entry)
        for user in room.users.values()
        for player_entry in user.squad
        if _squad_player_id(player_entry)
    }
    position_map: dict[str, str] = {}
    if squad_ids:
        squad_result = await db.execute(
            select(AuctionPlayer.id, AuctionPlayer.position).where(AuctionPlayer.id.in_(squad_ids))
        )
        position_map = {player_id: position for player_id, position in squad_result.all()}

    for user in room.users.values():
        if len(user.squad) != squad_size:
            return False

        counts = {"GK": 0, "DEF": 0, "MID": 0, "FWD": 0}
        for player_entry in user.squad:
            player_id = _squad_player_id(player_entry)
            position = position_map.get(player_id, "MID")
            if position in counts:
                counts[position] += 1

        for position, minimum in min_requirements.items():
            if counts[position] < minimum:
                return False

    return True


async def check_and_disqualify(room: AuctionRoom, db: AsyncSession) -> tuple[list[str], list[str]]:
    """
    Called when the host force-ends the auction.
    Checks every league member against min position + squad size requirements.
    Members that don't qualify are removed from league_members and squads.
    Returns (qualified_user_ids, disqualified_user_ids).
    """
    from sqlalchemy import delete as sql_delete

    league_result = await db.execute(
        select(League).where(League.id == uuid.UUID(room.league_id))
    )
    league = league_result.scalar_one_or_none()
    if not league:
        return list(room.users.keys()), []

    squad_size   = int(league.squad_size or 0)
    min_req = {
        "GK":  int(league.min_gk  or 0),
        "DEF": int(league.min_def or 0),
        "MID": int(league.min_mid or 0),
        "FWD": int(league.min_fwd or 0),
    }

    # Build position map for all players in any squad in this room
    squad_ids = {
        _squad_player_id(entry)
        for user in room.users.values()
        for entry in user.squad
        if _squad_player_id(entry)
    }
    position_map: dict[str, str] = {}
    if squad_ids:
        pos_result = await db.execute(
            select(AuctionPlayer.id, AuctionPlayer.position).where(AuctionPlayer.id.in_(squad_ids))
        )
        position_map = {pid: pos for pid, pos in pos_result.all()}

    qualified: list[str] = []
    disqualified: list[str] = []

    min_squad_size = sum(min_req.values())

    for user_id, user in room.users.items():
        counts = {"GK": 0, "DEF": 0, "MID": 0, "FWD": 0}
        for entry in user.squad:
            pid = _squad_player_id(entry)
            pos = position_map.get(pid, "MID")
            if pos in counts:
                counts[pos] += 1

        meets_requirements = (
            len(user.squad) >= min_squad_size and
            all(counts[pos] >= min_req[pos] for pos in min_req)
        )

        if meets_requirements:
            qualified.append(user_id)
        else:
            disqualified.append(user_id)
            # Remove from DB
            try:
                await db.execute(
                    sql_delete(Squad).where(
                        Squad.league_id == uuid.UUID(room.league_id),
                        Squad.user_id == user_id,
                    )
                )
                await db.execute(
                    sql_delete(LeagueMember).where(
                        LeagueMember.league_id == uuid.UUID(room.league_id),
                        LeagueMember.user_id == user_id,
                    )
                )
            except Exception as e:
                print(f"[ERROR] Failed to remove disqualified user {user_id}: {e}")

    try:
        await db.commit()
    except Exception as e:
        print(f"[ERROR] Failed to commit disqualifications: {e}")

    return qualified, disqualified



def cancel_timer(room: AuctionRoom, current_task: asyncio.Task | None = None) -> None:
    if room.timer_task and room.timer_task is not current_task and not room.timer_task.done():
        room.timer_task.cancel()
    room.timer_task = None


async def start_timer(room: AuctionRoom, seconds: int) -> None:
    try:
        for remaining in range(seconds, -1, -1):
            room.timer_seconds = remaining
            await broadcast(room, {
                "type": "timer_tick",
                "payload": {"seconds_left": remaining}
            })
            if remaining == 0:
                break
            await asyncio.sleep(1)

        if room.current_player_id and room.status == "bidding":
            await handle_player_sold(room)
    except asyncio.CancelledError:
        pass


def launch_timer(room: AuctionRoom, seconds: int) -> None:
    if room.timer_task and not room.timer_task.done():
        room.timer_task.cancel()
    room.timer_task = asyncio.create_task(start_timer(room, seconds))


async def handle_timer_expired(room: AuctionRoom) -> None:
    if room.current_player_id is None:
        return
    if room.status == "bidding":
        await handle_player_sold(room)


async def handle_nomination(room: AuctionRoom, player_id: str, nominator_id: str, db: AsyncSession) -> None:
    cached_player = next((player for player in room.nomination_queue_data if player.get("id") == player_id), None)
    if cached_player is not None:
        player = cached_player
    else:
        result = await db.execute(select(AuctionPlayer).where(AuctionPlayer.id == player_id))
        player = result.scalar_one_or_none()
    if not player:
        return
    if player_id in room.sold_players:
        return

    room.status = "bidding"
    room.current_player_id = player_id
    room.current_player = {
        "id": player["id"] if isinstance(player, dict) else player.id,
        "name": player["name"] if isinstance(player, dict) else player.name,
        "position": player["position"] if isinstance(player, dict) else player.position,
        "tier": player["tier"] if isinstance(player, dict) else player.tier,
        "base_price": player["base_price"] if isinstance(player, dict) else player.base_price,
        "market_value": player["market_value"] if isinstance(player, dict) else player.market_value,
        "flag_code": player["flag_code"] if isinstance(player, dict) else player.flag_code,
        "image_url": player["image_url"] if isinstance(player, dict) else player.image_url,
        "club": player["club"] if isinstance(player, dict) else player.club,
        "goals_2526": player["goals_2526"] if isinstance(player, dict) else player.goals_2526,
        "assists_2526": player["assists_2526"] if isinstance(player, dict) else player.assists_2526,
        "minutes_2526": player["minutes_2526"] if isinstance(player, dict) else player.minutes_2526,
        "form_score": player["form_score"] if isinstance(player, dict) else player.form_score,
    }
    room.current_high_bid = 0
    room.current_bidder_id = None
    room.has_received_bid = False
    room.status = "bidding"

    if room.timer_task and not room.timer_task.done():
        room.timer_task.cancel()
    room.timer_task = asyncio.create_task(start_timer(room, 60))

    # Build upcoming preview — next 3 unsold players after current
    upcoming = []
    preview_idx = room.queue_index + 1
    while len(upcoming) < 3 and preview_idx < len(room.nomination_queue_data):
        nxt = room.nomination_queue_data[preview_idx]
        if nxt["id"] not in room.sold_players:
            upcoming.append(
                {
                    "name": nxt["name"],
                    "position": nxt["position"],
                    "tier": nxt["tier"],
                    "flag_code": nxt["flag_code"],
                }
            )
        preview_idx += 1

    await broadcast(
        room,
        {
            "type": "player_nominated",
            "payload": {
                "player": room.current_player,
                "nominated_by": nominator_id,
                "current_bid": 0,
                "timer": 60,
                "upcoming": upcoming,
            },
        },
    )


async def _save_bid_background(league_id: uuid.UUID, player_id: str, user_id: str, amount: int) -> None:
    try:
        from app.core.database import PostgresSessionLocal
        async with PostgresSessionLocal() as session:
            bid = Bid(
                league_id=league_id,
                player_id=player_id,
                user_id=user_id,
                amount=amount,
            )
            session.add(bid)
            await session.commit()
    except Exception as e:
        print(f"[ERROR] Failed to save bid in background: {e}")


async def handle_bid(room: AuctionRoom, user_id: str, amount: int, db: AsyncSession) -> None:
    if room.status not in ("bidding", "active"):
        return
    user = room.users.get(user_id)
    if not user:
        return
    current_base_price = int(room.current_player.get("base_price") or 0) if room.current_player else 0
    if room.current_high_bid <= 0:
        if amount != current_base_price:
            await broadcast(
                room,
                {
                    "type": "bid_rejected",
                    "payload": {"reason": f"First bid must be exactly {current_base_price} coins"},
                },
            )
            return
    # Prevent current highest bidder from bidding again
    if user_id == room.current_bidder_id and room.current_high_bid > 0:
        return
    if amount <= room.current_high_bid:
        return
    if amount > user.budget_left:
        return
    if amount - room.current_high_bid < 10:
        return

    # Check league constraints using cached settings
    settings = getattr(room, "league_settings", None)
    if settings:
        if len(user.squad) >= settings["squad_size"]:
            connection = room.connections.get(user_id)
            if connection:
                await connection.send_json({
                    "type": "bid_rejected",
                    "payload": {"reason": f"Your squad is full ({settings['squad_size']} players max)"},
                })
            return

        current_player_pos = room.current_player.get("position", "MID") if room.current_player else "MID"
        max_for_this_pos = settings.get(f"max_{current_player_pos.lower()}", settings["squad_size"])

        # Count owned players of this position using cached player positions
        owned_this_pos = 0
        player_positions = getattr(room, "player_positions", {})
        for entry in user.squad:
            pid = _squad_player_id(entry)
            if pid and player_positions.get(pid) == current_player_pos:
                owned_this_pos += 1

        if owned_this_pos >= max_for_this_pos:
            connection = room.connections.get(user_id)
            if connection:
                await connection.send_json({
                    "type": "bid_rejected",
                    "payload": {
                        "reason": f"You already have the maximum {max_for_this_pos} {current_player_pos} players allowed",
                    },
                })
            return

    room.current_high_bid = amount
    room.current_bidder_id = user_id
    room.has_received_bid = True

    # Send immediate acknowledgment to the bidder so their UI updates instantly
    bidder_ws = room.connections.get(user_id)
    if bidder_ws:
        try:
            await bidder_ws.send_json({
                "type": "bid_ack",
                "payload": {"amount": amount, "status": "accepted"},
            })
        except Exception:
            pass

    # Save bid to database in the background to avoid blocking critical websocket path
    league_uuid = _as_uuid(room.league_id)
    if league_uuid:
        asyncio.create_task(
            _save_bid_background(
                league_uuid,
                room.current_player_id,
                user_id,
                amount,
            )
        )

    if room.timer_task and not room.timer_task.done():
        room.timer_task.cancel()
    room.timer_task = asyncio.create_task(start_timer(room, 30))

    await broadcast(
        room,
        {
            "type": "bid_placed",
            "payload": {
                "user_id": user_id,
                "username": user.username,
                "amount": amount,
                "timer_reset_to": 30,
            },
        },
    )

async def handle_player_sold(room: AuctionRoom) -> None:
    """Called when a timer expires. Uses its own DB session so it is fully
    decoupled from any WebSocket connection's lifetime."""
    if not room.current_player_id:
        return
    if room.status != "bidding":
        return

    room.status = "processing"
    winner_id = room.current_bidder_id
    price = room.current_high_bid
    player_id = room.current_player_id
    player = room.current_player
    winner_name = "No buyer"

    from app.core.database import PostgresSessionLocal
    async with PostgresSessionLocal() as db:
        try:
            if winner_id and winner_id in room.users and price and price > 0:
                room.users[winner_id].budget_left -= price
                room.users[winner_id].squad.append({"id": player_id, "purchase_price": price})

                winner_name = room.users[winner_id].username

                db.add(Squad(
                    league_id=uuid.UUID(room.league_id),
                    user_id=winner_id,
                    player_id=player_id,
                    purchase_price=price,
                ))
                await db.execute(
                    sql_update(LeagueMember)
                    .where(LeagueMember.league_id == uuid.UUID(room.league_id))
                    .where(LeagueMember.user_id == winner_id)
                    .values(
                        budget_spent=LeagueMember.budget_spent + price,
                        budget_left=LeagueMember.budget_left - price,
                    )
                )
                await db.commit()
                print(f"[SOLD] {player_id} to {winner_id} for {price}")
            else:
                winner_name = "No buyer"
                print(f"[WARN] No buyer for {player_id}")
        except Exception as e:
            winner_name = "No buyer"
            print(f"[ERROR] DB error in handle_player_sold: {e}")
            try:
                await db.rollback()
            except Exception:
                pass

        room.sold_players.append(player_id)

        await broadcast(room, {
            "type": "player_sold",
            "payload": {
                "player": player,
                "winner": winner_name,
                "price": price,
            },
        })

        room.current_player_id = None
        room.current_player = None
        room.current_high_bid = 0
        room.current_bidder_id = None
        room.has_received_bid = False

        await broadcast(room, {"type": "room_state", "payload": await _serialize_room_state(room, db)})

        if await all_squads_complete(room, db):
            room.status = "complete"
            await broadcast(room, {"type": "auction_complete", "payload": room.to_state()})
            try:
                await db.execute(
                    sql_update(League)
                    .where(League.id == uuid.UUID(room.league_id))
                    .values(status="active")
                )
                await db.commit()
                print(f"[OK] League {room.league_id} -> active")
            except Exception as e:
                print(f"[ERROR] Failed to activate league: {e}")
            return

        await asyncio.sleep(3)
        room.status = "active"

        advanced = False
        while room.queue_index + 1 < len(room.nomination_queue_data):
            room.queue_index += 1
            next_player = room.nomination_queue_data[room.queue_index]
            if next_player["id"] not in room.sold_players:
                advanced = True
                await handle_nomination(room, next_player["id"], "system", db)
                break

        if not advanced and room.queue_index + 1 >= len(room.nomination_queue_data):
            room.status = "complete"
            if await all_squads_complete(room, db):
                await broadcast(room, {"type": "auction_complete", "payload": room.to_state()})
                try:
                    await db.execute(
                        sql_update(League)
                        .where(League.id == uuid.UUID(room.league_id))
                        .values(status="active")
                    )
                    await db.commit()
                    print(f"[OK] League {room.league_id} -> active")
                except Exception as e:
                    print(f"[ERROR] Failed to activate league: {e}")
            else:
                await broadcast(room, {
                    "type": "auction_complete",
                    "payload": {
                        **room.to_state(),
                        "warning": "Player pool exhausted before all squads were filled.",
                    },
                })


async def handle_connection(
    league_id: str,
    user_id: str,
    username: str,
    websocket: WebSocket,
    db: AsyncSession,
):
    room = get_or_create_room(league_id)
    room.connections[user_id] = websocket

    # Initialize cache values for fast in-memory validation
    if not hasattr(room, "player_positions") or not room.player_positions:
        result = await db.execute(select(AuctionPlayer.id, AuctionPlayer.position))
        room.player_positions = {row[0]: row[1] for row in result.all()}

    if not hasattr(room, "league_settings") or room.league_settings is None:
        league_uuid = _as_uuid(room.league_id)
        if league_uuid:
            league_result = await db.execute(
                select(League).where(League.id == league_uuid)
            )
            league = league_result.scalar_one_or_none()
            if league:
                room.league_settings = {
                    "squad_size": league.squad_size,
                    "max_gk": league.max_gk if league.max_gk is not None else 3,
                    "max_def": league.max_def if league.max_def is not None else 6,
                    "max_mid": league.max_mid if league.max_mid is not None else 6,
                    "max_fwd": league.max_fwd if league.max_fwd is not None else 5,
                }
                room.host_id = league.host_id
            else:
                room.league_settings = None

    if user_id not in room.users:
        # Load budget from league_members
        member_result = await db.execute(
            select(LeagueMember)
            .where(LeagueMember.league_id == uuid.UUID(league_id))
            .where(LeagueMember.user_id == user_id)
        )
        member = member_result.scalar_one_or_none()
        budget = member.budget_left if member else 50000

        # Load existing squad from squads table
        squad_result = await db.execute(
            select(Squad.player_id, Squad.purchase_price)
            .where(Squad.league_id == uuid.UUID(league_id))
            .where(Squad.user_id == user_id)
        )
        existing_squad = [
            {"id": player_id, "purchase_price": purchase_price or 0}
            for player_id, purchase_price in squad_result.all()
        ]

        room.users[user_id] = RoomUser(
            user_id=user_id,
            username=username,
            budget_left=budget,
            squad=existing_squad,
        )
        if not hasattr(room, "nomination_order"):
            room.nomination_order = []
        if user_id not in room.nomination_order:
            room.nomination_order.append(user_id)

    await websocket.send_json({"type": "room_state", "payload": await _serialize_room_state(room, db)})
    await broadcast(room, {"type": "user_joined", "payload": {"user_id": user_id, "username": username}})
    await broadcast(room, {"type": "room_state", "payload": await _serialize_room_state(room, db)})

    # Sync sold_players from DB — ensures server restarts don't re-nominate already-sold players
    sold_result = await db.execute(
        select(Squad.player_id).where(Squad.league_id == uuid.UUID(league_id))
    )
    db_sold = [row[0] for row in sold_result.all()]
    for pid in db_sold:
        if pid not in room.sold_players:
            room.sold_players.append(pid)

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            payload = data.get("payload", {})

            if msg_type == "start_auction":
                if room.status != "waiting":
                    continue

                # Verify this user is the league host
                league_result = await db.execute(
                    select(League).where(League.id == uuid.UUID(room.league_id))
                )
                league = league_result.scalar_one_or_none()
                if not league or league.host_id != user_id:
                    connection = room.connections.get(user_id)
                    if connection:
                        await connection.send_json({
                            "type": "error",
                            "payload": {"message": "Only the league host can start the auction"}
                        })
                    continue

                result = await db.execute(select(AuctionPlayer))
                all_players = result.scalars().all()
                players_list = [
                    {
                        "id": p.id,
                        "name": p.name,
                        "position": p.position,
                        "tier": p.tier,
                        "base_price": p.base_price,
                        "market_value": p.market_value,
                        "flag_code": p.flag_code,
                        "image_url": p.image_url,
                        "club": p.club,
                        "goals_2526": p.goals_2526,
                        "assists_2526": p.assists_2526,
                        "minutes_2526": p.minutes_2526,
                        "form_score": p.form_score,
                    }
                    for p in all_players
                ]
                from app.services.auction_engine import build_nomination_queue

                # Pre-populate sold_players from DB before building queue
                sold_result = await db.execute(
                    select(Squad.player_id).where(Squad.league_id == uuid.UUID(room.league_id))
                )
                for (pid,) in sold_result.all():
                    if pid not in room.sold_players:
                        room.sold_players.append(pid)

                room.nomination_queue_data = build_nomination_queue(players_list)
                room.queue_index = 0
                room.status = "active"

                await broadcast(
                    room,
                    {
                        "type": "auction_started",
                        "payload": {
                            "total_players": len(room.nomination_queue_data),
                            "message": "Auction started — system will nominate players automatically",
                        },
                    },
                )

                await asyncio.sleep(2)
                if room.nomination_queue_data:
                    found = False
                    for idx, p in enumerate(room.nomination_queue_data):
                        if p["id"] not in room.sold_players:
                            room.queue_index = idx
                            found = True
                            await handle_nomination(room, p["id"], "system", db)
                            break
                    if not found:
                        room.status = "complete"
                        await broadcast(room, {"type": "auction_complete", "payload": await _serialize_room_state(room, db)})

            elif msg_type == "place_bid":
                await handle_bid(room, user_id, int(payload["amount"]), db)
            elif msg_type == "confirm_sale":
                cached_host = getattr(room, "host_id", None)
                if not cached_host or cached_host != user_id:
                    connection = room.connections.get(user_id)
                    if connection:
                        await connection.send_json({
                            "type": "error",
                            "payload": {"message": "Only the host can confirm a sale"}
                        })
                    continue

                if not room.has_received_bid or room.current_high_bid <= 0:
                    connection = room.connections.get(user_id)
                    if connection:
                        await connection.send_json({
                            "type": "error",
                            "payload": {"message": "Cannot confirm sale — no bids placed yet"}
                        })
                    continue

                if room.status != "bidding":
                    continue

                if room.timer_task and not room.timer_task.done():
                    room.timer_task.cancel()
                    room.timer_task = None

                await handle_player_sold(room)
            elif msg_type == "skip_player":
                # Only allow skipping when auction is active and current player has no bids
                if room.status != "bidding":
                    continue

                # Verify this user is the league host (cached)
                cached_host = getattr(room, "host_id", None)
                if not cached_host or cached_host != user_id:
                    connection = room.connections.get(user_id)
                    if connection:
                        await connection.send_json({
                            "type": "error",
                            "payload": {"message": "Only the league host can skip a player"}
                        })
                    continue

                # Cannot skip once a bid has been placed
                if room.current_high_bid and room.current_high_bid > 0:
                    connection = room.connections.get(user_id)
                    if connection:
                        await connection.send_json({
                            "type": "error",
                            "payload": {"message": "Cannot skip after a bid has been placed"}
                        })
                    continue

                # Perform skip: remove current player from future nominations
                if room.current_player_id:
                    skipped_player = room.current_player
                    room.sold_players.append(room.current_player_id)

                    # Clear current player state
                    room.current_player_id = None
                    room.current_player = None
                    room.current_high_bid = 0
                    room.current_bidder_id = None
                    room.has_received_bid = False

                    await broadcast(room, {
                        "type": "player_skipped",
                        "payload": {"player": skipped_player, "skipped_by": user_id},
                    })

                    await broadcast(room, {"type": "room_state", "payload": await _serialize_room_state(room, db)})

                    # Advance to next nomination
                    await asyncio.sleep(1)
                    advanced = False
                    while room.queue_index + 1 < len(room.nomination_queue_data):
                        room.queue_index += 1
                        next_player = room.nomination_queue_data[room.queue_index]
                        if next_player["id"] not in room.sold_players:
                            advanced = True
                            await handle_nomination(room, next_player["id"], "system", db)
                            break

                    if not advanced and room.queue_index + 1 >= len(room.nomination_queue_data):
                        room.status = "complete"
                        await broadcast(room, {"type": "auction_complete", "payload": await _serialize_room_state(room, db)})

            elif msg_type == "stop_auction":
                # Only the host can stop the auction
                cached_host = getattr(room, "host_id", None)
                if not cached_host or cached_host != user_id:
                    connection = room.connections.get(user_id)
                    if connection:
                        await connection.send_json({
                            "type": "error",
                            "payload": {"message": "Only the host can stop the auction"}
                        })
                    continue

                # Cancel any running timer
                cancel_timer(room)

                room.status = "complete"
                room.current_player_id = None
                room.current_player = None
                room.current_high_bid = 0
                room.current_bidder_id = None
                room.has_received_bid = False

                # Disqualify members whose rosters don't meet requirements
                qualified, disqualified = await check_and_disqualify(room, db)

                # Notify disqualified users individually
                for dq_user_id in disqualified:
                    dq_ws = room.connections.get(dq_user_id)
                    if dq_ws:
                        try:
                            await dq_ws.send_json({
                                "type": "disqualified",
                                "payload": {
                                    "message": "You have been disqualified — your roster did not meet the minimum requirements."
                                }
                            })
                        except Exception:
                            pass

                # Determine league outcome
                if not qualified:
                    # No eligible members — forfeit the league
                    new_status = "forfeited"
                    print(f"[WARN] League {room.league_id} forfeited — no qualifying members")
                else:
                    new_status = "active"
                    print(f"[OK] League {room.league_id} -> active ({len(qualified)} qualified, {len(disqualified)} disqualified)")

                try:
                    await db.execute(
                        sql_update(League)
                        .where(League.id == uuid.UUID(room.league_id))
                        .values(status=new_status)
                    )
                    await db.commit()
                except Exception as e:
                    print(f"[ERROR] Failed to set league {new_status} on stop: {e}")

                await broadcast(room, {
                    "type": "auction_complete",
                    "payload": {
                        **await _serialize_room_state(room, db),
                        "league_status": new_status,
                        "disqualified": disqualified,
                        "qualified": qualified,
                    },
                })
                print(f"[OK] Auction stopped by host {user_id}")

            elif msg_type == "pause_auction":
                # Only the host can pause the auction
                cached_host = getattr(room, "host_id", None)
                if not cached_host or cached_host != user_id:
                    continue
                if room.status != "bidding":
                    continue

                cancel_timer(room)
                room.status = "paused"
                await broadcast(room, {
                    "type": "auction_paused",
                    "payload": {
                        "seconds_left": getattr(room, "timer_seconds", 30),
                        "message": "Auction paused by host"
                    }
                })
                await broadcast(room, {
                    "type": "room_state",
                    "payload": await _serialize_room_state(room, db)
                })
                print(f"[OK] Auction paused by host {user_id}")

            elif msg_type == "resume_auction":
                # Only the host can resume the auction
                cached_host = getattr(room, "host_id", None)
                if not cached_host or cached_host != user_id:
                    continue
                if room.status != "paused":
                    continue

                room.status = "bidding"
                secs = getattr(room, "timer_seconds", 30)
                if secs <= 0:
                    secs = 30  # fallback
                launch_timer(room, secs)
                await broadcast(room, {
                    "type": "auction_resumed",
                    "payload": {
                        "seconds_left": secs,
                        "message": "Auction resumed by host"
                    }
                })
                await broadcast(room, {
                    "type": "room_state",
                    "payload": await _serialize_room_state(room, db)
                })
                print(f"[OK] Auction resumed by host {user_id}")

    except WebSocketDisconnect:
        room.connections.pop(user_id, None)
        await broadcast(room, {"type": "user_left", "payload": {"user_id": user_id, "username": username}})