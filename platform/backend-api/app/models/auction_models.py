from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func


AuctionBase = declarative_base()


class AuctionPlayer(AuctionBase):
    __tablename__ = "auction_players"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    nationality = Column(String)
    iso_code = Column(String(3))
    flag_code = Column(String(10))
    position = Column(String(3))
    sub_position = Column(String)
    club = Column(String)
    league = Column(String)
    age = Column(Float)
    market_value = Column(Float)
    base_price = Column(Integer)
    tier = Column(String)
    form_score = Column(Float)
    goals_2526 = Column(Integer)
    assists_2526 = Column(Integer)
    minutes_2526 = Column(Integer)
    matches_2526 = Column(Integer)
    goals_per_90 = Column(Float)
    assists_per_90 = Column(Float)
    ga_per_90 = Column(Float)
    yellow_cards = Column(Integer)
    red_cards = Column(Integer)
    image_url = Column(Text)
    international_caps = Column(Integer)
    val_date = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class League(AuctionBase):
    __tablename__ = "leagues"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    invite_code = Column(String(12), unique=True, nullable=False)
    host_id = Column(String, nullable=False)
    status = Column(String, default="auction")
    budget = Column(Integer, default=50000)
    squad_size = Column(Integer, default=20)
    min_gk = Column(Integer, default=2)
    min_def = Column(Integer, default=5)
    min_mid = Column(Integer, default=5)
    min_fwd = Column(Integer, default=3)
    max_gk = Column(Integer, default=3)
    max_def = Column(Integer, default=6)
    max_mid = Column(Integer, default=6)
    max_fwd = Column(Integer, default=5)
    scoring_rules = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class LeagueMember(AuctionBase):
    __tablename__ = "league_members"
    __table_args__ = (UniqueConstraint("league_id", "user_id"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    league_id = Column(UUID(as_uuid=True), ForeignKey("leagues.id"))
    user_id = Column(String, nullable=False)
    team_name = Column(String)
    budget_spent = Column(Integer, default=0)
    budget_left = Column(Integer)
    total_points = Column(Integer, default=0)
    is_disqualified = Column(Boolean, default=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())


class Squad(AuctionBase):
    __tablename__ = "squads"
    __table_args__ = (UniqueConstraint("league_id", "player_id"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    league_id = Column(UUID(as_uuid=True), ForeignKey("leagues.id"))
    user_id = Column(String, nullable=False)
    player_id = Column(String, ForeignKey("auction_players.id"))
    purchase_price = Column(Integer, nullable=False)
    acquired_at = Column(DateTime(timezone=True), server_default=func.now())


class AuctionSession(AuctionBase):
    __tablename__ = "auction_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    league_id = Column(UUID(as_uuid=True), ForeignKey("leagues.id"), unique=True)
    current_player_id = Column(String, ForeignKey("auction_players.id"), nullable=True)
    current_high_bid = Column(Integer, default=0)
    current_bidder_id = Column(String, nullable=True)
    timer_ends_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default="waiting")
    nomination_queue = Column(JSONB, default=list)
    nomination_order = Column(JSONB, default=list)
    current_nominator_idx = Column(Integer, default=0)


class Bid(AuctionBase):
    __tablename__ = "bids"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    league_id = Column(UUID(as_uuid=True), ForeignKey("leagues.id"))
    player_id = Column(String, ForeignKey("auction_players.id"))
    user_id = Column(String, nullable=False)
    amount = Column(Integer, nullable=False)
    placed_at = Column(DateTime(timezone=True), server_default=func.now())


class WCMatch(AuctionBase):
    __tablename__ = "wc_matches"

    id = Column(String, primary_key=True)
    stage = Column(String)
    home_code = Column(String(3))
    away_code = Column(String(3))
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    played_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default="scheduled")


class PlayerPerformance(AuctionBase):
    __tablename__ = "player_performances"
    __table_args__ = (UniqueConstraint("match_id", "player_id"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id = Column(String, ForeignKey("wc_matches.id"))
    player_id = Column(String, ForeignKey("auction_players.id"))
    goals = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    minutes_played = Column(Integer, default=0)
    yellow_cards = Column(Integer, default=0)
    red_cards = Column(Integer, default=0)
    clean_sheet = Column(Boolean, default=False)
    saves = Column(Integer, default=0)
    goals_conceded = Column(Integer, default=0)
    penalties_scored = Column(Integer, default=0)
    penalties_missed = Column(Integer, default=0)
    penalties_saved = Column(Integer, default=0)
    player_rating = Column(Float, nullable=True)
    raw_points = Column(Integer, default=0)


class LeaderboardSnapshot(AuctionBase):
    __tablename__ = "leaderboard_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    league_id = Column(UUID(as_uuid=True), ForeignKey("leagues.id"))
    user_id = Column(String, nullable=False)
    match_id = Column(String, ForeignKey("wc_matches.id"))
    points_this_match = Column(Integer, default=0)
    cumulative_points = Column(Integer, default=0)
    rank_at_snapshot = Column(Integer)
    snapshot_at = Column(DateTime(timezone=True), server_default=func.now())


class User(AuctionBase):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())