from __future__ import annotations

import os
import uuid
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "DATA"
BACKEND_ENV_PATH = PROJECT_ROOT / "platform" / "backend-api" / ".env"
PROCESSED_DIR = PROJECT_ROOT / "platform" / "data" / "processed"
OUTPUT_CSV = PROCESSED_DIR / "auction_players.csv"

PLAYERS_CSV = DATA_DIR / "transfer market" / "players.csv"
VALUATIONS_CSV = DATA_DIR / "transfer market" / "player_valuations.csv"
SEASON_CSV = DATA_DIR / "latest" / "players_data-2025_2026.csv"

FLAG_MAP = {
    "ESP": "es",
    "FRA": "fr",
    "GER": "de",
    "BRA": "br",
    "ARG": "ar",
    "POR": "pt",
    "NED": "nl",
    "BEL": "be",
    "ENG": "gb-eng",
    "ITA": "it",
    "CRO": "hr",
    "SUI": "ch",
    "TUR": "tr",
    "USA": "us",
    "MEX": "mx",
    "CAN": "ca",
    "MAR": "ma",
    "SEN": "sn",
    "NGA": "ng",
    "CMR": "cm",
    "EGY": "eg",
    "JPN": "jp",
    "KOR": "kr",
    "AUS": "au",
    "KSA": "sa",
    "IRN": "ir",
    "ALG": "dz",
    "GHA": "gh",
    "CIV": "ci",
    "URU": "uy",
    "COL": "co",
    "ECU": "ec",
    "PER": "pe",
    "DEN": "dk",
    "POL": "pl",
    "SRB": "rs",
    "GEO": "ge",
    "ALB": "al",
    "UKR": "ua",
    "TUN": "tn",
    "MLI": "ml",
    "RSA": "za",
    "COD": "cd",
    "QAT": "qa",
    "IRQ": "iq",
    "ISR": "il",
    "NZL": "nz",
    "BOL": "bo",
    "PAR": "py",
    "VEN": "ve",
    "CHI": "cl",
    "HON": "hn",
    "JAM": "jm",
    "CRC": "cr",
    "NOR": "no",
    "SCO": "sco",
    "WAL": "gb-wls",
    "AUT": "at",
    "CZE": "cz",
    "SVK": "sk",
    "SVN": "si",
    "FIN": "fi",
    "SWE": "se",
    "IRL": "ie",
    "GRE": "gr",
    "ROU": "ro",
    "BUL": "bg",
    "ISL": "is",
    "CYP": "cy",
    "LUX": "lu",
    "MKD": "mk",
    "MNE": "me",
    "BIH": "ba",
    "KOS": "xk",
    "AND": "ad",
    "MLT": "mt",
    "LIE": "li",
    "MDG": "mg",
    "BFA": "bf",
    "GNB": "gw",
    "GAB": "ga",
    "BEN": "bj",
    "TOG": "tg",
    "GUI": "gn",
    "SLE": "sl",
    "LBR": "lr",
    "GNQ": "gq",
    "CPV": "cv",
    "COM": "km",
    "MRT": "mr",
    "MOZ": "mz",
    "ZIM": "zw",
    "ZAM": "zm",
    "MWI": "mw",
    "RWA": "rw",
    "UGA": "ug",
    "TAN": "tz",
    "KEN": "ke",
    "ETH": "et",
    "SOM": "so",
    "DJI": "dj",
    "ERI": "er",
    "LBA": "ly",
    "SUD": "sd",
    "CHA": "td",
    "NIG": "ne",
    "MLW": "mw",
    "JAP": "jp",
    "PHI": "ph",
    "THA": "th",
    "VIE": "vn",
    "IND": "in",
    "PAK": "pk",
    "BAN": "bd",
    "SRI": "lk",
    "NEP": "np",
    "BHU": "bt",
    "PAN": "pa",
    "GUA": "gt",
    "CUB": "cu",
    "DOM": "do",
    "HAI": "ht",
    "TRI": "tt",
    "BAR": "bb",
    "ATG": "ag",
    "KVX": "xk",
    "ANG": "ao",
    "HUN": "hu",
    "NIR": "gb-nir",
    "MTN": "me",
    "GAM": "gm",
    "IDN": "id",
    "SUR": "sr",
    "RUS": "ru",
    "CTA": "cf",
    "LBY": "ly",
    "MAD": "mg",
    "GLP": "gp",
    "EQG": "gq",
    "ARM": "am",
    "EST": "ee",
    "BDI": "bi",
    "CGO": "cg",
    "BRB": "bb",
    "GUF": "gf",
    "MTQ": "mq",
    "UZB": "uz",
    "LTU": "lt",
    "MAS": "my",
    "FRO": "fo",
    "LVA": "lv",
    "JOR": "jo",
}


def load_backend_env(env_path: Path) -> None:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=False)


def normalize_pos(pos: object) -> str:
    if pd.isna(pos):
        return "MID"
    primary = str(pos).split(",")[0].strip()
    return {"GK": "GK", "DF": "DEF", "MF": "MID", "FW": "FWD"}.get(primary, "MID")


def assign_tier(value: float) -> tuple[str, int]:
    if value >= 50_000_000:
        return "Elite", 1000
    if value >= 20_000_000:
        return "World Class", 600
    if value >= 5_000_000:
        return "Quality", 300
    if value >= 1_000_000:
        return "Rotation", 150
    return "Depth", 75


def build_name_keys(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().str.strip()


def latest_values_by_player(values: pd.DataFrame) -> pd.DataFrame:
    working = values.copy()
    working["player_id"] = working["player_id"].astype(str)
    working["date"] = pd.to_datetime(working["date"], errors="coerce")
    working = working.sort_values("date")
    return (
        working.groupby("player_id", as_index=False)
        .last()[["player_id", "date", "market_value_in_eur"]]
        .rename(columns={"date": "val_date", "market_value_in_eur": "latest_market_value"})
    )


def ensure_uuid(value: object) -> str:
    if pd.isna(value) or value in (None, "", "nan", "NaN"):
        return str(uuid.uuid4())
    try:
        return str(int(float(value)))
    except Exception:
        return str(value)


def build_dataset() -> pd.DataFrame:
    if not PLAYERS_CSV.exists():
        raise FileNotFoundError(f"Missing base file: {PLAYERS_CSV}")
    if not VALUATIONS_CSV.exists():
        raise FileNotFoundError(f"Missing valuation file: {VALUATIONS_CSV}")
    if not SEASON_CSV.exists():
        raise FileNotFoundError(f"Missing season file: {SEASON_CSV}")

    season = pd.read_csv(SEASON_CSV)
    print(f"2025-26 players loaded: {len(season)}")

    season["iso_code"] = season["Nation"].astype(str).str.extract(r"\s(\w{2,3})$")[0].str.upper()
    season["flag_code"] = season["iso_code"].map(FLAG_MAP).fillna("un")
    season["canonical_pos"] = season["Pos"].apply(normalize_pos)
    season["name_lower"] = build_name_keys(season["Player"])

    players = pd.read_csv(PLAYERS_CSV)
    players["player_id"] = players["player_id"].astype(str)
    players["name_lower"] = build_name_keys(players["name"])
    players = players.drop_duplicates(subset=["name_lower"], keep="first")

    player_fields = [
        "player_id",
        "name_lower",
        "country_of_citizenship",
        "image_url",
        "date_of_birth",
        "international_caps",
        "international_goals",
        "current_national_team_id",
        "sub_position",
        "foot",
        "height_in_cm",
    ]

    merged = season.merge(players[player_fields], on="name_lower", how="left", indicator=True)
    name_matches = int((merged["_merge"] == "both").sum())
    print(f"After name join to players.csv: {name_matches}")
    merged = merged.drop(columns=["_merge"])

    valuations = pd.read_csv(VALUATIONS_CSV)
    valuations["player_id"] = valuations["player_id"].astype(str)
    latest_val = latest_values_by_player(valuations)
    merged = merged.merge(latest_val, on="player_id", how="left")
    valuation_matches = int(merged["latest_market_value"].notna().sum())
    print(f"After valuation join: {valuation_matches}")

    pos_medians = merged.groupby("canonical_pos")["latest_market_value"].median()
    merged["latest_market_value"] = merged.apply(
        lambda row: pos_medians.get(row["canonical_pos"], pd.NA)
        if pd.isna(row["latest_market_value"])
        else row["latest_market_value"],
        axis=1,
    )

    merged[["tier", "base_price"]] = merged["latest_market_value"].apply(
        lambda value: pd.Series(assign_tier(float(value) if pd.notna(value) else 0.0))
    )

    merged["goals_per_90"] = (pd.to_numeric(merged["Gls"], errors="coerce").fillna(0) / pd.to_numeric(merged["90s"], errors="coerce").replace(0, pd.NA)).fillna(0).round(2)
    merged["assists_per_90"] = (pd.to_numeric(merged["Ast"], errors="coerce").fillna(0) / pd.to_numeric(merged["90s"], errors="coerce").replace(0, pd.NA)).fillna(0).round(2)
    merged["ga_per_90"] = (pd.to_numeric(merged["G+A"], errors="coerce").fillna(0) / pd.to_numeric(merged["90s"], errors="coerce").replace(0, pd.NA)).fillna(0).round(2)

    merged["form_score"] = (
        merged["goals_per_90"] * 40
        + merged["assists_per_90"] * 25
        + (pd.to_numeric(merged["Min"], errors="coerce").fillna(0) / 3060) * 20
        + (pd.to_numeric(merged["MP"], errors="coerce").fillna(0) / 38) * 15
    ).clip(0, 100).round(2)

    merged["age"] = pd.to_numeric(merged["Age"], errors="coerce")
    merged["goals_2526"] = pd.to_numeric(merged["Gls"], errors="coerce").fillna(0).astype(int)
    merged["assists_2526"] = pd.to_numeric(merged["Ast"], errors="coerce").fillna(0).astype(int)
    merged["minutes_2526"] = pd.to_numeric(merged["Min"], errors="coerce").fillna(0).astype(int)
    merged["matches_2526"] = pd.to_numeric(merged["MP"], errors="coerce").fillna(0).astype(int)
    merged["yellow_cards"] = pd.to_numeric(merged["CrdY"], errors="coerce").fillna(0).astype(int)
    merged["red_cards"] = pd.to_numeric(merged["CrdR"], errors="coerce").fillna(0).astype(int)

    merged["id"] = merged["player_id"].apply(ensure_uuid)
    merged["created_at"] = pd.Timestamp.utcnow()

    final = pd.DataFrame(
        {
            "id": merged["id"],
            "name": merged["Player"].astype(str).str.strip(),
            "nationality": merged["country_of_citizenship"],
            "iso_code": merged["iso_code"],
            "flag_code": merged["flag_code"],
            "position": merged["canonical_pos"],
            "sub_position": merged["sub_position"],
            "club": merged["Squad"],
            "league": merged["Comp"],
            "age": merged["age"],
            "market_value": pd.to_numeric(merged["latest_market_value"], errors="coerce"),
            "base_price": merged["base_price"].astype(int),
            "tier": merged["tier"],
            "form_score": merged["form_score"],
            "goals_2526": merged["goals_2526"],
            "assists_2526": merged["assists_2526"],
            "minutes_2526": merged["minutes_2526"],
            "matches_2526": merged["matches_2526"],
            "goals_per_90": merged["goals_per_90"],
            "assists_per_90": merged["assists_per_90"],
            "ga_per_90": merged["ga_per_90"],
            "yellow_cards": merged["yellow_cards"],
            "red_cards": merged["red_cards"],
            "image_url": merged["image_url"],
            "international_caps": pd.to_numeric(merged["international_caps"], errors="coerce"),
            "val_date": pd.to_datetime(merged["val_date"], errors="coerce").dt.strftime("%Y-%m-%d"),
            "created_at": merged["created_at"],
        }
    )

    final["id"] = final["id"].astype(str)
    final["name"] = final["name"].fillna("").astype(str).str.strip()
    final["nationality"] = final["nationality"].fillna("")
    final["iso_code"] = final["iso_code"].fillna("")
    final["flag_code"] = final["flag_code"].fillna("un")
    final["position"] = final["position"].fillna("MID")
    final["sub_position"] = final["sub_position"].fillna("")
    final["club"] = final["club"].fillna("")
    final["league"] = final["league"].fillna("")
    final["market_value"] = pd.to_numeric(final["market_value"], errors="coerce").fillna(0)
    final["base_price"] = pd.to_numeric(final["base_price"], errors="coerce").fillna(75).astype(int)
    final["tier"] = final["tier"].fillna("Depth")
    final["form_score"] = pd.to_numeric(final["form_score"], errors="coerce").fillna(0).round(2)
    final["goals_per_90"] = pd.to_numeric(final["goals_per_90"], errors="coerce").fillna(0).round(2)
    final["assists_per_90"] = pd.to_numeric(final["assists_per_90"], errors="coerce").fillna(0).round(2)
    final["ga_per_90"] = pd.to_numeric(final["ga_per_90"], errors="coerce").fillna(0).round(2)
    final["international_caps"] = pd.to_numeric(final["international_caps"], errors="coerce").fillna(0).astype(int)
    final["created_at"] = pd.to_datetime(final["created_at"], utc=True)

    final["id"] = final["id"].apply(lambda value: str(value) if pd.notna(value) else str(uuid.uuid4()))
    final = final.sort_values("market_value", ascending=False).drop_duplicates(subset="id", keep="first")
    final = final.sort_values("market_value", ascending=False).drop_duplicates(subset="name", keep="first")
    print(f"After dedup: {len(final)} rows, {final['id'].duplicated().sum()} duplicate IDs")

    tier_distribution = final["tier"].value_counts(dropna=False).to_dict()
    print(f"Tier distribution: {tier_distribution}")

    final = final[
        [
            "id",
            "name",
            "nationality",
            "iso_code",
            "flag_code",
            "position",
            "sub_position",
            "club",
            "league",
            "age",
            "market_value",
            "base_price",
            "tier",
            "form_score",
            "goals_2526",
            "assists_2526",
            "minutes_2526",
            "matches_2526",
            "goals_per_90",
            "assists_per_90",
            "ga_per_90",
            "yellow_cards",
            "red_cards",
            "image_url",
            "international_caps",
            "val_date",
            "created_at",
        ]
    ]

    print(f"Missing player IDs after join: {final['id'].isna().sum():,}")
    print(f"flag_code = \"un\" count: {(final['flag_code'] == 'un').sum():,}")
    haaland = final[final["name"].str.contains("Haaland", case=False, na=False)]
    if not haaland.empty:
        print(f"Haaland flag_code: {haaland.iloc[0]['flag_code']}")
    return final


def load_backend_env_and_write(df_final: pd.DataFrame) -> None:
    load_backend_env(BACKEND_ENV_PATH)
    supabase_url = os.getenv("SUPABASE_POSTGRES_URL")
    if not supabase_url:
        raise RuntimeError(
            f"SUPABASE_POSTGRES_URL not found. Expected it in {BACKEND_ENV_PATH} or the environment."
        )

    engine = create_engine(
        supabase_url,
        connect_args={"connect_timeout": 20, "sslmode": "require"},
        pool_pre_ping=True,
    )
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS auction_players (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    nationality TEXT,
                    iso_code TEXT,
                    flag_code TEXT,
                    position TEXT,
                    sub_position TEXT,
                    club TEXT,
                    league TEXT,
                    age DOUBLE PRECISION,
                    market_value DOUBLE PRECISION,
                    base_price INTEGER,
                    tier TEXT,
                    form_score DOUBLE PRECISION,
                    goals_2526 INTEGER,
                    assists_2526 INTEGER,
                    minutes_2526 INTEGER,
                    matches_2526 INTEGER,
                    goals_per_90 DOUBLE PRECISION,
                    assists_per_90 DOUBLE PRECISION,
                    ga_per_90 DOUBLE PRECISION,
                    yellow_cards INTEGER,
                    red_cards INTEGER,
                    image_url TEXT,
                    international_caps INTEGER,
                    val_date TEXT,
                    created_at TIMESTAMPTZ DEFAULT now()
                )
                """
            )
        )
        connection.execute(text("TRUNCATE TABLE auction_players"))

    df_final.to_sql(
        "auction_players",
        engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=500,
    )
    print(f"Loaded {len(df_final)} players to Supabase auction_players table")


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df_final = build_dataset()
    df_final.to_csv(OUTPUT_CSV, index=False)
    print(f"Saved local backup to {OUTPUT_CSV}")
    load_backend_env_and_write(df_final)


if __name__ == "__main__":
    main()