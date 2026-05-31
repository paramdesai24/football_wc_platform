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


async def broadcast(room: AuctionRoom, message: dict) -> None:
    print(f"Broadcasting {message.get('type')} to {len(room.connections)} connections")
    dead = []
    for user_id, websocket in room.connections.items():
        try:
            await websocket.send_json(message)
        except Exception:
            dead.append(user_id)
    for user_id in dead:
        room.connections.pop(user_id, None)


async def _serialize_room_state(room: AuctionRoom, db: AsyncSession) -> dict:
    state = room.to_state()
    squad_ids = {
        player_id
        for user in room.users.values()
        for player_id in user.squad
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
            "squad": [
                {"id": player_id, "position": position_map.get(player_id, "MID")}
                for player_id in room.users[user_id].squad
            ] if user_id in room.users else [],
        }
        for user_id, user_state in state.get("users", {}).items()
    }
    return state


def cancel_timer(room: AuctionRoom, current_task: asyncio.Task | None = None) -> None:
    if room.timer_task and room.timer_task is not current_task and not room.timer_task.done():
        room.timer_task.cancel()
    room.timer_task = None


async def start_timer(room: AuctionRoom, seconds: int, db: AsyncSession) -> None:
    try:
        for remaining in range(seconds, -1, -1):
            await broadcast(room, {
                "type": "timer_tick",
                "payload": {"seconds_left": remaining}
            })
            if remaining == 0:
                break
            await asyncio.sleep(1)

        if room.current_player_id and room.status == "bidding":
            await handle_player_sold(room, db)
    except asyncio.CancelledError:
        pass


def launch_timer(room: AuctionRoom, seconds: int, db: AsyncSession) -> None:
    if room.timer_task and not room.timer_task.done():
        room.timer_task.cancel()
    room.timer_task = asyncio.create_task(start_timer(room, seconds, db))


async def handle_timer_expired(room: AuctionRoom, db: AsyncSession) -> None:
    if room.current_player_id is None:
        return
    if room.status == "bidding":
        await handle_player_sold(room, db)


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
    room.timer_task = asyncio.create_task(start_timer(room, 60, db))

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

    league_uuid = _as_uuid(room.league_id)
    if league_uuid:
        league_result = await db.execute(
            select(League).where(League.id == league_uuid)
        )
        league = league_result.scalar_one_or_none()
        if league:
            if len(user.squad) >= league.squad_size:
                connection = room.connections.get(user_id)
                if connection:
                    await connection.send_json({
                        "type": "bid_rejected",
                        "payload": {"reason": f"Your squad is full ({league.squad_size} players max)"},
                    })
                return

            current_player_pos = room.current_player.get("position", "MID") if room.current_player else "MID"
            min_by_pos = {
                "GK": league.min_gk,
                "DEF": league.min_def,
                "MID": league.min_mid,
                "FWD": league.min_fwd,
            }
            total_min = league.min_gk + league.min_def + league.min_mid + league.min_fwd
            other_mins = total_min - min_by_pos.get(current_player_pos, 0)
            max_for_this_pos = max(0, league.squad_size - other_mins)

            owned_ids = user.squad
            if owned_ids:
                pos_result = await db.execute(
                    select(AuctionPlayer)
                    .where(AuctionPlayer.id.in_(owned_ids))
                    .where(AuctionPlayer.position == current_player_pos)
                )
                owned_this_pos = len(pos_result.scalars().all())
            else:
                owned_this_pos = 0

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

    league_uuid = _as_uuid(room.league_id)
    if league_uuid:
        bid = Bid(
            league_id=league_uuid,
            player_id=room.current_player_id,
            user_id=user_id,
            amount=amount,
        )
        db.add(bid)
        await db.commit()

    if room.timer_task and not room.timer_task.done():
        room.timer_task.cancel()
    room.timer_task = asyncio.create_task(start_timer(room, 30, db))

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
async def handle_player_sold(room: AuctionRoom, db: AsyncSession) -> None:
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

    try:
        if winner_id and winner_id in room.users and price and price > 0:
            room.users[winner_id].budget_left -= price
            room.users[winner_id].squad.append(player_id)

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
            print(f"✅ Sold {player_id} to {winner_id} for {price}")
        else:
            winner_name = "No buyer"
            print(f"⚠️ No buyer for {player_id}")
    except Exception as e:
        winner_name = "No buyer"
        print(f"❌ DB error: {e}")
        await db.rollback()

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
        await broadcast(room, {"type": "auction_complete", "payload": await _serialize_room_state(room, db)})


async def handle_connection(
    league_id: str,
    user_id: str,
    username: str,
    websocket: WebSocket,
    db: AsyncSession,
):
    room = get_or_create_room(league_id)
    room.connections[user_id] = websocket

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
            select(Squad.player_id)
            .where(Squad.league_id == uuid.UUID(league_id))
            .where(Squad.user_id == user_id)
        )
        existing_squad = [row[0] for row in squad_result.all()]

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
                    first = room.nomination_queue_data[0]
                    await handle_nomination(room, first["id"], "system", db)

            elif msg_type == "place_bid":
                await handle_bid(room, user_id, int(payload["amount"]), db)

    except WebSocketDisconnect:
        room.connections.pop(user_id, None)
        await broadcast(room, {"type": "user_left", "payload": {"user_id": user_id}})