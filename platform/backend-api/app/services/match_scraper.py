import os
import httpx
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent.parent / ".env")

# ── football-data.org (match results + scorers) ──────────────
FD_TOKEN   = os.getenv("FOOTBALL_DATA_TOKEN", "")
FD_BASE    = "https://api.football-data.org/v4"
FD_WC_ID   = 2000
FD_HEADERS = {"X-Auth-Token": FD_TOKEN}

# ── API-Football (full player stats) ─────────────────────────
AF_TOKEN   = os.getenv("API_FOOTBALL_TOKEN", "")
AF_BASE    = "https://v3.football.api-sports.io"
# FIFA World Cup ID on API-Football.
# Before WC 2026 starts, verify with:
#   GET https://v3.football.api-sports.io/leagues?name=FIFA World Cup&season=2026
#   Header: x-apisports-key: <YOUR_KEY>
# Use the `id` field from the response to update this constant.
AF_WC_ID   = 1
AF_HEADERS = {"x-apisports-key": AF_TOKEN}


# ── football-data.org helpers ─────────────────────────────────

async def fd_fetch_completed_matches() -> list[dict]:
    if not FD_TOKEN:
        raise ValueError("FOOTBALL_DATA_TOKEN not set in .env")
    url = f"{FD_BASE}/competitions/{FD_WC_ID}/matches?status=FINISHED"
    print(f"[FD] Fetching completed matches: {url}")
    async with httpx.AsyncClient(timeout=15) as client:
        res = await client.get(url, headers=FD_HEADERS)
        print(f"[FD] Status: {res.status_code}")
        if res.status_code != 200:
            print(f"[FD] Error: {res.text[:300]}")
        res.raise_for_status()
    return res.json().get("matches", [])


def fd_parse_match(raw: dict) -> dict:
    home  = raw.get("homeTeam", {})
    away  = raw.get("awayTeam", {})
    score = raw.get("score", {}).get("fullTime", {})
    return {
        "match_id":       f"WC2026_{raw['id']}",
        "fd_match_id":    raw["id"],
        "stage":          raw.get("stage", "GROUP_STAGE").replace("_", " ").title(),
        "home_code":      home.get("tla", "").upper(),
        "away_code":      away.get("tla", "").upper(),
        "home_score":     score.get("home", 0) or 0,
        "away_score":     score.get("away", 0) or 0,
        "played_at":      raw.get("utcDate"),
        "home_team_name": home.get("name", ""),
        "away_team_name": away.get("name", ""),
    }


def fd_parse_scorers(match_detail: dict) -> list[dict]:
    """Extract goal/assist events from a football-data.org match detail response."""
    goals  = match_detail.get("goals", [])
    events: dict[str, dict] = {}
    for g in goals:
        scorer = g.get("scorer", {})
        assist = g.get("assist")
        team   = g.get("team", {})
        tla    = team.get("tla", "").upper()
        if scorer and scorer.get("name"):
            n = scorer["name"]
            if n not in events:
                events[n] = {"name": n, "team_code": tla, "goals": 0, "assists": 0}
            events[n]["goals"] += 1
        if assist and assist.get("name"):
            n = assist["name"]
            if n not in events:
                events[n] = {"name": n, "team_code": tla, "goals": 0, "assists": 0}
            events[n]["assists"] += 1
    return list(events.values())


async def fd_fetch_match_detail(fd_match_id: int) -> dict:
    url = f"{FD_BASE}/matches/{fd_match_id}"
    async with httpx.AsyncClient(timeout=15) as client:
        res = await client.get(url, headers=FD_HEADERS)
        res.raise_for_status()
    return res.json()


# ── API-Football helpers ──────────────────────────────────────

async def af_find_fixture(home_name: str, away_name: str, played_at: str) -> int | None:
    """
    Find the API-Football fixture ID by team names and match date.
    Returns None if the token is absent or the fixture cannot be found.
    """
    if not AF_TOKEN:
        print("[AF] API_FOOTBALL_TOKEN not set — skipping enrichment")
        return None

    date_str = played_at[:10] if played_at else ""
    url = f"{AF_BASE}/fixtures?league={AF_WC_ID}&season=2026&date={date_str}"
    print(f"[AF] Finding fixture for {home_name} vs {away_name} on {date_str}")
    async with httpx.AsyncClient(timeout=15) as client:
        res = await client.get(url, headers=AF_HEADERS)
        print(f"[AF] Fixtures status: {res.status_code}")
        if res.status_code != 200:
            print(f"[AF] Error: {res.text[:300]}")
            return None
    fixtures = res.json().get("response", [])
    for f in fixtures:
        h = f.get("teams", {}).get("home", {}).get("name", "").lower()
        a = f.get("teams", {}).get("away", {}).get("name", "").lower()
        if home_name.lower() in h or h in home_name.lower():
            if away_name.lower() in a or a in away_name.lower():
                fixture_id = f["fixture"]["id"]
                print(f"[AF] Found fixture ID: {fixture_id}")
                return fixture_id
    print(f"[AF] No fixture found for {home_name} vs {away_name}")
    return None


async def af_fetch_player_stats(fixture_id: int) -> list[dict]:
    """
    Fetch full player statistics for a fixture from API-Football.
    Only includes players who recorded playing time (minutes > 0).
    """
    url = f"{AF_BASE}/fixtures/players?fixture={fixture_id}"
    print(f"[AF] Fetching player stats for fixture {fixture_id}")
    async with httpx.AsyncClient(timeout=15) as client:
        res = await client.get(url, headers=AF_HEADERS)
        print(f"[AF] Player stats status: {res.status_code}")
        if res.status_code != 200:
            print(f"[AF] Error: {res.text[:300]}")
            return []
    response = res.json().get("response", [])
    players = []
    for team_block in response:
        team_code = team_block.get("team", {}).get("code", "").upper()
        for p in team_block.get("players", []):
            info  = p.get("player", {})
            stats = p.get("statistics", [{}])[0]
            games = stats.get("games", {})
            goals = stats.get("goals", {})
            cards = stats.get("cards", {})

            minutes = games.get("minutes") or 0
            # Only include players who actually played
            if minutes == 0:
                continue

            rating_str = games.get("rating")
            player_rating = None
            if rating_str:
                try:
                    player_rating = float(rating_str)
                except (ValueError, TypeError):
                    pass

            players.append({
                "name":             info.get("name", ""),
                "team_code":        team_code,
                "minutes":          minutes,
                "goals":            goals.get("total") or 0,
                "assists":          goals.get("assists") or 0,
                "yellow_cards":     cards.get("yellow") or 0,
                "red_cards":        cards.get("red") or 0,
                "saves":            stats.get("goalkeeper", {}).get("saves") or 0,
                "goals_conceded":   goals.get("conceded") or 0,
                "penalties_scored": stats.get("penalty", {}).get("scored") or 0,
                "penalties_missed": stats.get("penalty", {}).get("missed") or 0,
                "penalties_saved":  stats.get("penalty", {}).get("saved") or 0,
                "player_rating":    player_rating,
                # clean_sheet is computed later from match score
            })
    print(f"[AF] Got stats for {len(players)} players")
    return players


def compute_clean_sheet(
    player_name: str,
    team_code: str,
    home_code: str,
    away_code: str,
    home_score: int,
    away_score: int,
) -> bool:
    """A player earns a clean sheet if their team conceded 0 goals."""
    if team_code == home_code:
        return away_score == 0
    if team_code == away_code:
        return home_score == 0
    return False


# ── Unified scraper ───────────────────────────────────────────

# Global status tracking object for match scraper cron
SCRAPER_STATUS = {
    "last_successful_run": None,
    "next_scheduled_run": None,
    "fixtures_processed_in_last_run": 0,
    "players_processed_in_last_run": 0,
    "total_fixtures_processed": 0,
    "total_players_processed": 0,
    "status": "idle",
    "error_message": None,
}


async def scrape_match_full(parsed: dict) -> list[dict]:
    """
    Combine football-data.org scorers with API-Football full player stats.

    Strategy:
    - API-Football is the primary source for minutes, cards, saves.
    - football-data.org goal/assist events are merged on top for accuracy,
      since FD is generally more reliable for WC goal attribution.
    - Falls back to FD-only if AF token is absent or fixture not found;
      in that case minutes default to 90, cards/saves/clean_sheets are 0.

    Returns a list of player performance dicts ready for DB insert.
    """
    # Step 1: pull goal/assist events from football-data.org
    fd_detail  = await fd_fetch_match_detail(parsed["fd_match_id"])
    fd_scorers = fd_parse_scorers(fd_detail)

    # Build a quick lookup by lowercase name for merge step
    scorer_map = {s["name"].lower(): s for s in fd_scorers}

    # Step 2: try to get full stats from API-Football
    af_players: list[dict] = []
    if AF_TOKEN:
        fixture_id = await af_find_fixture(
            parsed["home_team_name"],
            parsed["away_team_name"],
            parsed.get("played_at", ""),
        )
        if fixture_id:
            af_players = await af_fetch_player_stats(fixture_id)

    performances: list[dict] = []

    if af_players:
        # PRIMARY PATH — API-Football has minutes/cards/saves
        for p in af_players:
            name_lower = p["name"].lower()
            # Overlay FD goal/assist counts where available (more reliable)
            fd_match = scorer_map.get(name_lower, {})
            goals   = fd_match.get("goals",   p["goals"])
            assists = fd_match.get("assists",  p["assists"])

            clean_sheet = compute_clean_sheet(
                p["name"], p["team_code"],
                parsed["home_code"], parsed["away_code"],
                parsed["home_score"], parsed["away_score"],
            )

            performances.append({
                "name":             p["name"],
                "team_code":        p["team_code"],
                "goals":            goals,
                "assists":          assists,
                "minutes":          p["minutes"],
                "yellow_cards":     p["yellow_cards"],
                "red_cards":        p["red_cards"],
                "saves":            p["saves"],
                "goals_conceded":   p["goals_conceded"],
                "penalties_scored": p["penalties_scored"],
                "penalties_missed": p["penalties_missed"],
                "penalties_saved":  p["penalties_saved"],
                "player_rating":    p["player_rating"],
                "clean_sheet":      clean_sheet,
                "source":           "api_football",
            })
    else:
        # FALLBACK PATH — football-data.org scorers only
        # minutes default to 90; no cards, no clean sheets
        for s in fd_scorers:
            performances.append({
                "name":             s["name"],
                "team_code":        s["team_code"],
                "goals":            s["goals"],
                "assists":          s["assists"],
                "minutes":          90,
                "yellow_cards":     0,
                "red_cards":        0,
                "saves":            0,
                "goals_conceded":   0,
                "penalties_scored": 0,
                "penalties_missed": 0,
                "penalties_saved":  0,
                "player_rating":    None,
                "clean_sheet":      False,
                "source":           "football_data_fallback",
            })
        print(f"[SCRAPER] Using fallback (FD only) for match {parsed['match_id']}")

    return performances


# ── Legacy aliases (kept for backward compatibility) ──────────
# The old scrape endpoint imported these names directly.
fetch_completed_matches = fd_fetch_completed_matches
parse_match             = fd_parse_match
parse_goal_scorers      = fd_parse_scorers
fetch_match_lineups     = fd_fetch_match_detail