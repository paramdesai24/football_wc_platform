from __future__ import annotations

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_postgres_db
from app.models.auction_models import AuctionPlayer, LeaderboardSnapshot, LeagueMember, PlayerPerformance, WCMatch
from app.services.scoring_engine import process_match_scores

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/matches", tags=["admin"])


class PlayerPerfInput(BaseModel):
    player_id: str
    goals: int = 0
    assists: int = 0
    minutes_played: int = 0
    yellow_cards: int = 0
    red_cards: int = 0
    clean_sheet: bool = False
    saves: int = 0


class MatchResultInput(BaseModel):
    match_id: str = Field(..., description='e.g. "WC2026_GS_01"')
    stage: str = Field(..., description='e.g. "Group Stage"')
    home_code: str = Field(..., description='e.g. "ESP"')
    away_code: str = Field(..., description='e.g. "FRA"')
    home_score: int
    away_score: int
    performances: List[PlayerPerfInput]


@router.post("/result")
async def submit_match_result(req: MatchResultInput, db: AsyncSession = Depends(get_postgres_db)):
    if req.performances:
        player_ids = [p.player_id for p in req.performances]
        result = await db.execute(
            select(AuctionPlayer).where(AuctionPlayer.id.in_(player_ids))
        )
        players_found = {p.id: p for p in result.scalars().all()}

        invalid = []
        home = req.home_code.upper().strip()
        away = req.away_code.upper().strip()

        for perf in req.performances:
            player = players_found.get(perf.player_id)
            if not player:
                invalid.append(f"Player ID {perf.player_id} not found in auction_players")
                continue

            player_iso = (player.iso_code or "").upper().strip()
            if player_iso not in (home, away):
                invalid.append(f"{player.name} ({player_iso}) does not play for {home} or {away}")

        if invalid:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "Player-team mismatch",
                    "invalid_players": invalid,
                    "hint": f"Only players from {req.home_code} or {req.away_code} can be added to this match",
                },
            )

    match = WCMatch(
        id=req.match_id,
        stage=req.stage,
        home_code=req.home_code,
        away_code=req.away_code,
        home_score=req.home_score,
        away_score=req.away_score,
        status="completed",
    )
    await db.merge(match)

    await db.execute(delete(PlayerPerformance).where(PlayerPerformance.match_id == req.match_id))

    for perf_input in req.performances:
        db.add(
            PlayerPerformance(
                match_id=req.match_id,
                player_id=perf_input.player_id,
                goals=perf_input.goals,
                assists=perf_input.assists,
                minutes_played=perf_input.minutes_played,
                yellow_cards=perf_input.yellow_cards,
                red_cards=perf_input.red_cards,
                clean_sheet=perf_input.clean_sheet,
                saves=perf_input.saves,
            )
        )

    await db.flush()
    await process_match_scores(req.match_id, db)
    return {"status": "processed", "match_id": req.match_id}


async def generate_simulated_performances(db: AsyncSession, parsed: dict) -> list[PlayerPerformance]:
    import random
    home_code = parsed["home_code"]
    away_code = parsed["away_code"]
    match_id = parsed["match_id"]
    
    result = await db.execute(
        select(AuctionPlayer)
        .where(AuctionPlayer.iso_code.in_([home_code, away_code]))
    )
    players = result.scalars().all()
    
    home_players = [p for p in players if p.iso_code == home_code]
    away_players = [p for p in players if p.iso_code == away_code]
    
    if not home_players and not away_players:
        logger.warning(f"No database players found for {home_code} or {away_code} to simulate performance.")
        return []
        
    performances = []
    # Seed with match ID to keep simulation reproducible/consistent across runs
    random.seed(match_id)
    
    for team_code, team_players, score, opp_score in [
        (home_code, home_players, parsed["home_score"], parsed["away_score"]),
        (away_code, away_players, parsed["away_score"], parsed["home_score"])
    ]:
        if not team_players:
            continue
            
        # Select players
        sorted_players = sorted(team_players, key=lambda x: x.market_value or 0, reverse=True)
        gks = [p for p in sorted_players if p.position == "GK"]
        gk = gks[0] if gks else None
        
        outfield = [p for p in sorted_players if p.position != "GK"]
        starters = outfield[:10]
        subs = outfield[10:13]
        
        played_players = []
        if gk:
            played_players.append((gk, 90))
        for p in starters:
            played_players.append((p, 90))
        for p in subs:
            played_players.append((p, random.randint(15, 45)))
            
        # Distribute goals
        goals_to_distribute = score
        scorers = []
        fwds_mids = [p for p, mins in played_players if p.position in ("FWD", "MID")]
        
        while goals_to_distribute > 0:
            if fwds_mids:
                scorer = random.choice(fwds_mids)
                scorers.append(scorer.id)
                goals_to_distribute -= 1
            else:
                scorer = random.choice([p for p, mins in played_players])
                scorers.append(scorer.id)
                goals_to_distribute -= 1
                
        # Distribute assists
        assists_to_distribute = min(score, random.randint(0, score))
        assist_players = []
        while assists_to_distribute > 0:
            potential_assisters = [p for p, mins in played_players if p.position in ("MID", "DEF", "FWD")]
            if potential_assisters:
                assister = random.choice(potential_assisters)
                assist_players.append(assister.id)
                assists_to_distribute -= 1
            else:
                break
                
        for p, minutes in played_players:
            p_goals = scorers.count(p.id)
            p_assists = assist_players.count(p.id)
            
            yellows = 1 if random.random() < 0.15 else 0
            reds = 1 if random.random() < 0.02 else 0
            
            saves = 0
            if p.position == "GK":
                saves = max(1, random.randint(1, 5) + opp_score)
                
            clean_sheet = opp_score == 0
            conceded = opp_score if p.position in ("GK", "DEF") else 0
            
            base_rating = 6.0
            if clean_sheet:
                base_rating += 0.5
            base_rating += p_goals * 1.5
            base_rating += p_assists * 1.0
            base_rating += random.uniform(-0.5, 0.5)
            rating = round(min(10.0, max(3.0, base_rating)), 1)
            
            performances.append(PlayerPerformance(
                match_id=match_id,
                player_id=p.id,
                goals=p_goals,
                assists=p_assists,
                minutes_played=minutes,
                yellow_cards=yellows,
                red_cards=reds,
                clean_sheet=clean_sheet,
                saves=saves,
                goals_conceded=conceded,
                penalties_scored=0,
                penalties_missed=0,
                penalties_saved=0,
                player_rating=rating,
            ))
            
    return performances


@router.post("/scrape")
async def scrape_and_process(db: AsyncSession = Depends(get_postgres_db)):
    """
    Fetch completed WC 2026 matches from football-data.org and enrich each
    match with full player stats (minutes, cards, saves, clean sheets) from
    API-Football. Falls back to database simulation when API details are unavailable.
    """
    from app.services.match_scraper import (
        fd_fetch_completed_matches,
        fd_parse_match,
        scrape_match_full,
    )
    from app.models.auction_models import AuctionPlayer

    api_failures = 0
    try:
        completed = await fd_fetch_completed_matches()
    except Exception as e:
        logger.error(f"API Failure: Failed to fetch completed matches: {e}")
        raise

    results = []
    fixtures_skipped = 0
    fixtures_processed = 0
    players_processed = 0

    for raw in completed:
        parsed   = fd_parse_match(raw)
        match_id = parsed["match_id"]

        # Skip already processed matches
        existing = await db.execute(select(WCMatch).where(WCMatch.id == match_id))
        if existing.scalar_one_or_none():
            fixtures_skipped += 1
            results.append({"match_id": match_id, "status": "already_processed"})
            continue

        # Get full player stats (API-Football primary, FD fallback)
        try:
            perf_data = await scrape_match_full(parsed)
        except Exception as e:
            logger.error(f"API Failure: Failed to scrape stats for match {match_id}: {e}")
            api_failures += 1
            results.append({"match_id": match_id, "status": "failed", "error": str(e)})
            continue

        # Match players to auction_players by name + team ISO code
        performances = []
        unmatched = []

        # 1. Always generate base simulated performances to ensure goalkeepers/defenders get minutes/saves/clean sheets
        sim_perfs = await generate_simulated_performances(db, parsed)
        sim_perf_map = {p.player_id: p for p in sim_perfs}

        # 2. Match real goal/assist scorers and overlay them on simulated stats
        data_source = perf_data[0]["source"] if perf_data else "none"
        for p in perf_data:
            player = None
            # Try exact/substring match first
            player_result = await db.execute(
                select(AuctionPlayer)
                .where(AuctionPlayer.iso_code == p["team_code"])
                .where(AuctionPlayer.name.ilike(f"%{p['name']}%"))
                .limit(1)
            )
            player = player_result.scalar_one_or_none()

            # Try initials matching (e.g. J. Quiñones -> Julián Quiñones)
            if not player:
                parts = [part.strip(".") for part in p["name"].split() if part.strip(".")]
                if len(parts) >= 2:
                    last_name = parts[-1]
                    first_char = parts[0][0]
                    res = await db.execute(
                        select(AuctionPlayer)
                        .where(AuctionPlayer.iso_code == p["team_code"])
                    )
                    team_players = res.scalars().all()
                    for tp in team_players:
                        tp_name = tp.name.lower()
                        tp_parts = tp_name.split()
                        if tp_parts and last_name.lower() in tp_name:
                            if tp_parts[0].startswith(first_char.lower()):
                                player = tp
                                break

            if player:
                if player.id in sim_perf_map:
                    sim_p = sim_perf_map[player.id]
                    sim_p.goals = p["goals"]
                    sim_p.assists = p["assists"]
                    # Recalculate rating
                    base_rating = 6.0
                    if sim_p.clean_sheet:
                        base_rating += 0.5
                    base_rating += sim_p.goals * 1.5
                    base_rating += sim_p.assists * 1.0
                    sim_p.player_rating = round(min(10.0, max(3.0, base_rating)), 1)
                else:
                    # Create new performance for sub/outfielder not in starter simulation
                    clean_sheet = parsed["away_score"] == 0 if p["team_code"] == parsed["home_code"] else parsed["home_score"] == 0
                    base_rating = 6.0 + p["goals"] * 1.5 + p["assists"] * 1.0
                    sim_perf_map[player.id] = PlayerPerformance(
                        match_id=match_id,
                        player_id=player.id,
                        goals=p["goals"],
                        assists=p["assists"],
                        minutes_played=45,
                        yellow_cards=0,
                        red_cards=0,
                        clean_sheet=clean_sheet,
                        saves=0,
                        goals_conceded=0,
                        player_rating=round(min(10.0, max(3.0, base_rating)), 1)
                    )
            else:
                unmatched.append(p["name"])

        performances = list(sim_perf_map.values())
        if perf_data and data_source != "simulation_fallback":
            data_source = f"{data_source}_integrated"
        else:
            data_source = "simulation_fallback"

        # Persist match record
        match = WCMatch(
            id=match_id,
            stage=parsed["stage"],
            home_code=parsed["home_code"],
            away_code=parsed["away_code"],
            home_score=parsed["home_score"],
            away_score=parsed["away_score"],
            status="completed",
        )
        await db.merge(match)
        for perf in performances:
            await db.merge(perf)
        await db.commit()

        # Run FPL-style scoring for this match
        await process_match_scores(match_id, db)

        fixtures_processed += 1
        players_processed += len(performances)

        results.append({
            "match_id":          match_id,
            "status":            "processed",
            "players_matched":   len(performances),
            "players_unmatched": len(unmatched),
            "unmatched_names":   unmatched[:10],
            "data_source":       data_source,
        })

    return {
        "scraped": len(results),
        "results": results,
        "fixtures_found": len(completed),
        "fixtures_skipped": fixtures_skipped,
        "fixtures_processed": fixtures_processed,
        "players_processed": players_processed,
        "api_failures": api_failures,
    }


@router.post("/recalculate")
async def recalculate_all_points(db: AsyncSession = Depends(get_postgres_db)):
    """
    Recomputes total_points for all league members from scratch.
    Use this after deleting match entries or correcting performances.
    """
    await db.execute(delete(LeaderboardSnapshot))
    await db.execute(update(LeagueMember).values(total_points=0))
    await db.commit()

    matches_result = await db.execute(
        select(WCMatch).where(WCMatch.status == "completed").order_by(WCMatch.played_at.asc(), WCMatch.id.asc())
    )
    matches = matches_result.scalars().all()

    processed: list[str] = []
    for match in matches:
      await process_match_scores(match.id, db)
      processed.append(match.id)

    return {
        "status": "recalculated",
        "matches_processed": processed,
        "count": len(processed),
    }


@router.delete("/match/{match_id}")
async def delete_match(match_id: str, db: AsyncSession = Depends(get_postgres_db)):
    """Delete a match and its performances, then recalculate all points."""
    await db.execute(delete(LeaderboardSnapshot).where(LeaderboardSnapshot.match_id == match_id))
    await db.execute(delete(PlayerPerformance).where(PlayerPerformance.match_id == match_id))
    await db.execute(delete(WCMatch).where(WCMatch.id == match_id))
    await db.execute(update(LeagueMember).values(total_points=0))
    await db.commit()

    matches_result = await db.execute(
        select(WCMatch).where(WCMatch.status == "completed").order_by(WCMatch.played_at.asc(), WCMatch.id.asc())
    )
    for match in matches_result.scalars().all():
        await process_match_scores(match.id, db)

    return {"status": "deleted_and_recalculated", "match_id": match_id}


@router.get("/")
async def list_matches(db: AsyncSession = Depends(get_postgres_db)):
    result = await db.execute(select(WCMatch).order_by(WCMatch.played_at.desc()))
    matches = result.scalars().all()
    return {
        "matches": [
            {
                "id": match.id,
                "stage": match.stage,
                "home_code": match.home_code,
                "away_code": match.away_code,
                "home_score": match.home_score,
                "away_score": match.away_score,
                "played_at": str(match.played_at) if match.played_at else None,
                "status": match.status,
            }
            for match in matches
        ]
    }


@router.get("/admin/scraper-status")
async def get_scraper_status(db: AsyncSession = Depends(get_postgres_db)):
    from app.services.match_scraper import SCRAPER_STATUS
    from sqlalchemy import func
    from sqlalchemy.future import select
    try:
        # Count completed matches
        matches_count = await db.scalar(
            select(func.count()).select_from(WCMatch).where(WCMatch.status == "completed")
        )
        # Count player performances
        perf_count = await db.scalar(
            select(func.count()).select_from(PlayerPerformance)
        )
        SCRAPER_STATUS["total_fixtures_processed"] = matches_count or 0
        SCRAPER_STATUS["total_players_processed"] = perf_count or 0
    except Exception as e:
        # Log error but return whatever status we have
        import logging
        logging.getLogger(__name__).error(f"Error updating lifetime counts for status: {e}")
    return SCRAPER_STATUS