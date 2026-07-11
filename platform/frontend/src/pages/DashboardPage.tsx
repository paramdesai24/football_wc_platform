import { useEffect, useState } from "react";
import type { CountryRankingRow } from "@/contracts";
import { apiGet, API_BASE } from "@/services/api";
import { USE_MOCKS } from "@/dev/devFlags";
import { getMockCountryRankings } from "@/dev/mockResponses";
import { teamFlagCode } from "@/lib/flags";

const HERO_IMAGE_URL = "/worldcup_hero_section.jpg";

export default function DashboardPage() {
  const [rankings, setRankings] = useState<CountryRankingRow[]>([]);

  // New state
  const [topPlayers, setTopPlayers] = useState<any[]>([]);
  const [featuredNationIdx, setFeaturedNationIdx] = useState(0);
  // Analytics compare — real attack/defence from the analytics endpoint
  const [analyticsTeams, setAnalyticsTeams] = useState<any[]>([]);

  const CACHE_TTL_MS = 60 * 60 * 1000; // 1 hour

  // Existing data fetches
  useEffect(() => {
    // 1. Check cache first
    try {
      const cached = localStorage.getItem("dashboard_rankings_cache");
      if (cached) {
        const { data, timestamp } = JSON.parse(cached);
        if (Date.now() - timestamp < CACHE_TTL_MS) {
          setRankings(data);
          return;
        }
      }
    } catch {}

    apiGet<{ data?: CountryRankingRow[] }>("/api/v1/countries/rankings?limit=16").then((res) => {
      if (res.error || !res.data) {
        if (USE_MOCKS) {
          setRankings(getMockCountryRankings());
        } else {
          setRankings([]);
        }
        return;
      }
      const rows = Array.isArray(res.data) ? res.data : (res.data as { data?: CountryRankingRow[] }).data;
      if (rows && rows.length > 0) {
        setRankings(rows);
        try {
          localStorage.setItem("dashboard_rankings_cache", JSON.stringify({ data: rows, timestamp: Date.now() }));
        } catch {}
      } else if (USE_MOCKS) {
        setRankings(getMockCountryRankings());
      } else {
        setRankings([]);
      }
    });
  }, []);


  // Fetch top Elite players
  useEffect(() => {
    // Check cache first
    try {
      const cached = localStorage.getItem("dashboard_top_players_cache");
      if (cached) {
        const { data, timestamp } = JSON.parse(cached);
        if (Date.now() - timestamp < CACHE_TTL_MS) {
          setTopPlayers(data);
          return;
        }
      }
    } catch {}

    fetch(`${API_BASE}/api/v1/auction/players?tier=Elite&limit=10`)
      .then(r => r.json())
      .then(d => {
        const players = d.players ?? [];
        setTopPlayers(players);
        try {
          localStorage.setItem("dashboard_top_players_cache", JSON.stringify({ data: players, timestamp: Date.now() }));
        } catch {}
      })
      .catch(() => {});
  }, []);

  // Fetch real attack/defence ratings from analytics compare endpoint
  // Only use top 8 teams by ELO — avoids inflated ratings on lower-ranked nations
  useEffect(() => {
    if (rankings.length === 0) return;
    const top8ByElo = [...rankings]
      .sort((a, b) => (b.elo_rating ?? 0) - (a.elo_rating ?? 0))
      .slice(0, 8);
    const uids = top8ByElo.map(r => r.country_uid).join(',');

    // Check cache first
    const cacheKey = `dashboard_compare_cache_${uids}`;
    try {
      const cached = localStorage.getItem(cacheKey);
      if (cached) {
        const { data, timestamp } = JSON.parse(cached);
        if (Date.now() - timestamp < CACHE_TTL_MS) {
          setAnalyticsTeams(data);
          return;
        }
      }
    } catch {}

    fetch(`${API_BASE}/api/v1/analytics/compare?team_ids=${encodeURIComponent(uids)}`)
      .then(r => r.json())
      .then(d => {
        if (Array.isArray(d.data) && d.data.length > 0) {
          setAnalyticsTeams(d.data);
          try {
            localStorage.setItem(cacheKey, JSON.stringify({ data: d.data, timestamp: Date.now() }));
          } catch {}
        }
      })
      .catch(() => {});
  }, [rankings]);

  // Rotating featured nation — cycle every 6 seconds
  useEffect(() => {
    if (!rankings || rankings.length === 0) return;
    const id = setInterval(() => {
      setFeaturedNationIdx(i => (i + 1) % Math.min(rankings.length, 8));
    }, 6000);
    return () => clearInterval(id);
  }, [rankings]);

  // Derived — use correct field names from CountryRankingRow
  const featuredNation = rankings[featuredNationIdx] ?? null;

  // Most Valuable Squads: sort by elo_rating descending (not the pre-computed rank)
  const squadsByElo = [...rankings].sort((a, b) => (b.elo_rating ?? 0) - (a.elo_rating ?? 0));

  // Use analytics compare data (real values) when available, fall back to rankings
  const analyticsSrc = analyticsTeams.length > 0 ? analyticsTeams : squadsByElo.slice(0, 8).map(r => ({
    country_id:   r.country_uid,
    country_name: r.country_name,
    attack:  r.attack_rating ?? 0,
    defense: r.defense_rating ?? 0,
  }));

  const bestAttackAnalytics  = [...analyticsSrc].sort((a, b) => (b.attack  ?? 0) - (a.attack  ?? 0))[0];
  const bestDefenseAnalytics = [...analyticsSrc].sort((a, b) => (b.defense ?? 0) - (a.defense ?? 0))[0];

  // Match analytics team back to the rankings row (for flag code via country_uid)
  const findRankRow = (uid: string | undefined) =>
    rankings.find(r => r.country_uid === uid);

  const bestAttackRow  = findRankRow(bestAttackAnalytics?.country_id);
  const bestDefenseRow = findRankRow(bestDefenseAnalytics?.country_id);

  const darkHorse   = rankings.find((_, i) => i >= 5 && i <= 8) ?? rankings[5];
  const favourite   = rankings[0];

  const maxElo = squadsByElo[0]?.elo_rating ?? 2200;

  return (
    <div style={{ maxWidth: 1280, margin: "0 auto", padding: "0 20px 40px" }}>

      {/* ══════════════════════════════════════════════ */}
      {/* SECTION 1 — HERO                              */}
      {/* ══════════════════════════════════════════════ */}
      <div style={{
        position:       "relative",
        borderRadius:   20,
        overflow:       "hidden",
        marginBottom:   20,
        minHeight:      320,
        display:        "flex",
        alignItems:     "center",
        padding:        "48px 52px",
        background:     "rgba(10,18,34,0.72)",
        backdropFilter: "blur(16px)",
        border:         "1px solid rgba(255,255,255,0.09)",
      }}>
        {/* Background — Messi fills the entire card, gradients handle blending */}
        <div style={{
          position:      "absolute",
          inset:         0,
          zIndex:        0,
          pointerEvents: "none",
        }}>
          {/* Image underneath everything */}
          <img
            src={HERO_IMAGE_URL}
            alt="FIFA World Cup"
            style={{
              width:          "100%",
              height:         "100%",
              objectFit:      "cover",
              objectPosition: "65% center",
              display:        "block",
              filter:         "brightness(0.65) saturate(0.8)",
            }}
          />
          {/* Left text-protection fade — solid for first 40%, then dissolves */}
          <div style={{
            position:   "absolute",
            inset:      0,
            background: "linear-gradient(to right, rgba(10,18,34,1) 0%, rgba(10,18,34,0.97) 20%, rgba(10,18,34,0.8) 35%, rgba(10,18,34,0.4) 52%, rgba(10,18,34,0.05) 70%, transparent 85%)",
          }} />
          {/* Top edge fade */}
          <div style={{
            position:   "absolute",
            inset:      0,
            background: "linear-gradient(to bottom, rgba(10,18,34,0.65) 0%, transparent 35%)",
          }} />
          {/* Bottom edge fade */}
          <div style={{
            position:   "absolute",
            inset:      0,
            background: "linear-gradient(to top, rgba(10,18,34,0.75) 0%, transparent 40%)",
          }} />
          {/* Right edge fade */}
          <div style={{
            position:   "absolute",
            inset:      0,
            background: "linear-gradient(to left, rgba(10,18,34,0.55) 0%, transparent 30%)",
          }} />
        </div>

        {/* Left — text, sits on top of the background layer */}
        <div style={{ flex: 1, zIndex: 1, position: "relative" }}>
          <div style={{
            fontSize: 11, fontWeight: 600, letterSpacing: "0.18em",
            textTransform: "uppercase", color: "rgba(212,175,55,0.8)",
            marginBottom: 14, fontFamily: "var(--font-ui)",
          }}>
            FIFA WORLD CUP 2026 · INTELLIGENCE CENTER
          </div>
          <div style={{
            fontFamily: "var(--font-ui)", fontSize: "clamp(32px,4vw,56px)",
            fontWeight: 800, color: "#ffffff", letterSpacing: "-0.02em",
            lineHeight: 1.05, marginBottom: 20,
          }}>
            The World Cup,<br />Decoded.
          </div>
          {/* Stat pills */}
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 28 }}>
            {[
              { label: "Nations",         value: "48" },
              { label: "Auction Players", value: "1,191" },
              { label: "Matches",         value: "104" },
            ].map(s => (
              <div key={s.label} style={{
                background:    "rgba(255,255,255,0.07)",
                border:        "1px solid rgba(255,255,255,0.1)",
                borderRadius:  10,
                padding:       "10px 18px",
                display:       "flex",
                flexDirection: "column",
                gap:           2,
              }}>
                <span style={{ fontFamily: "var(--font-display)", fontSize: 26, fontWeight: 800, color: "#ffffff", lineHeight: 1 }}>
                  {s.value}
                </span>
                <span style={{ fontSize: 11, color: "rgba(255,255,255,0.45)", fontFamily: "var(--font-ui)" }}>
                  {s.label}
                </span>
              </div>
            ))}
          </div>
          {/* CTA buttons */}
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
            <a href="/auction" style={{
              padding: "11px 26px", background: "#d4af37", borderRadius: 9,
              color: "#0a0f1a", fontFamily: "var(--font-ui)", fontSize: 14,
              fontWeight: 700, textDecoration: "none", display: "inline-block",
            }}>
              Enter Auction →
            </a>
            <a href="/predictions" style={{
              padding: "11px 26px", background: "transparent",
              border: "1px solid rgba(255,255,255,0.2)", borderRadius: 9,
              color: "#ffffff", fontFamily: "var(--font-ui)", fontSize: 14,
              fontWeight: 500, textDecoration: "none", display: "inline-block",
            }}>
              Match Predictions
            </a>
          </div>
        </div>
      </div>


      {/* ══════════════════════════════════════════════════════════ */}
      {/* SECTIONS 3 + 4 — TOP TARGETS + MOST VALUABLE SQUADS ROW  */}
      {/* ══════════════════════════════════════════════════════════ */}
      <div className="dashboard-main-grid" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 20 }}>

        {/* TOP AUCTION TARGETS */}
        <div style={{
          background:     "rgba(10,18,34,0.72)",
          backdropFilter: "blur(16px)",
          border:         "1px solid rgba(255,255,255,0.09)",
          borderRadius:   16,
          padding:        "20px 24px",
        }}>
          <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: "0.14em", textTransform: "uppercase", color: "rgba(212,175,55,0.75)", marginBottom: 4, fontFamily: "var(--font-ui)" }}>
            TOP AUCTION TARGETS ⭐
          </div>
          <div style={{ fontSize: 18, fontWeight: 700, color: "#fff", fontFamily: "var(--font-ui)", marginBottom: 16 }}>
            Elite players to watch
          </div>
          {topPlayers.slice(0, 6).map((p, i) => (
            <div key={p.id ?? i} style={{
              display:      "flex",
              alignItems:   "center",
              gap:          12,
              padding:      "10px 0",
              borderBottom: i < 5 ? "1px solid rgba(255,255,255,0.05)" : "none",
            }}>
              <span style={{ fontFamily: "var(--font-display)", fontSize: 14, fontWeight: 700, color: "rgba(255,255,255,0.25)", width: 20, textAlign: "right", flexShrink: 0 }}>
                {i + 1}
              </span>
              {p.image_url ? (
                <img src={p.image_url} alt={p.name} style={{ width: 36, height: 36, borderRadius: "50%", objectFit: "cover", flexShrink: 0, border: "1px solid rgba(255,255,255,0.1)" }} />
              ) : (
                <div style={{ width: 36, height: 36, borderRadius: "50%", background: "rgba(255,255,255,0.06)", flexShrink: 0, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 16 }}>⚽</div>
              )}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  {p.flag_code && (
                    <img src={`https://flagcdn.com/w40/${p.flag_code}.png`} style={{ width: 16, height: 11, objectFit: "cover", borderRadius: 2 }} alt="" />
                  )}
                  <span style={{ fontSize: 14, fontWeight: 600, color: "#fff", fontFamily: "var(--font-ui)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {p.name}
                  </span>
                </div>
                <span style={{ fontSize: 11, color: "rgba(255,255,255,0.4)", fontFamily: "var(--font-ui)" }}>
                  {p.position} · {p.club}
                </span>
              </div>
              <div style={{ textAlign: "right", flexShrink: 0 }}>
                <div style={{ fontFamily: "var(--font-display)", fontSize: 15, fontWeight: 700, color: "#d4af37" }}>
                  {p.base_price?.toLocaleString()}
                </div>
                <div style={{ fontSize: 10, color: "rgba(255,255,255,0.35)", fontFamily: "var(--font-ui)" }}>coins</div>
              </div>
            </div>
          ))}
          {topPlayers.length === 0 && (
            <div style={{ color: "rgba(255,255,255,0.35)", fontSize: 13, fontFamily: "var(--font-ui)", padding: "16px 0" }}>
              Loading elite players…
            </div>
          )}
          <a href="/auction/info" style={{ display: "block", marginTop: 12, fontSize: 12, color: "rgba(212,175,55,0.7)", textDecoration: "none", fontFamily: "var(--font-ui)", textAlign: "right" }}>
            View all players →
          </a>
        </div>

        {/* MOST VALUABLE SQUADS */}
        <div style={{
          background:     "rgba(10,18,34,0.72)",
          backdropFilter: "blur(16px)",
          border:         "1px solid rgba(255,255,255,0.09)",
          borderRadius:   16,
          padding:        "20px 24px",
        }}>
          <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: "0.14em", textTransform: "uppercase", color: "rgba(212,175,55,0.75)", marginBottom: 4, fontFamily: "var(--font-ui)" }}>
            MOST VALUABLE SQUADS 💰
          </div>
          <div style={{ fontSize: 18, fontWeight: 700, color: "#fff", fontFamily: "var(--font-ui)", marginBottom: 16 }}>
            By transfer market value
          </div>
          {squadsByElo.slice(0, 8).map((team, i) => {
            const flagCode = teamFlagCode(team.country_uid);
            const pct      = Math.round(((team.elo_rating ?? 0) / maxElo) * 100);
            const barColor = i === 0 ? "#d4af37" : i < 3 ? "#22c55e" : "#3b82f6";
            return (
              <div key={team.country_uid} style={{ marginBottom: 10 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
                  <span style={{ fontFamily: "var(--font-display)", fontSize: 13, fontWeight: 700, color: "rgba(255,255,255,0.3)", width: 18, textAlign: "right", flexShrink: 0 }}>
                    {i + 1}
                  </span>
                  {flagCode ? (
                    <img src={`https://flagcdn.com/w40/${flagCode}.png`} style={{ width: 20, height: 14, objectFit: "cover", borderRadius: 2 }} alt="" />
                  ) : (
                    <div style={{ width: 20, height: 14, background: "rgba(255,255,255,0.1)", borderRadius: 2 }} />
                  )}
                  <span style={{ flex: 1, fontSize: 14, fontWeight: 600, color: "#fff", fontFamily: "var(--font-ui)" }}>
                    {team.country_name}
                  </span>
                  <span style={{ fontFamily: "var(--font-display)", fontSize: 15, fontWeight: 700, color: "#fff" }}>
                    {team.elo_rating ? Math.round(team.elo_rating).toLocaleString() : "—"}
                  </span>
                </div>
                <div style={{ height: 4, borderRadius: 2, background: "rgba(255,255,255,0.07)", marginLeft: 28 }}>
                  <div style={{ height: 4, borderRadius: 2, width: `${pct}%`, background: barColor, transition: "width 0.6s ease" }} />
                </div>
              </div>
            );
          })}
          {rankings.length === 0 && (
            <div style={{ color: "rgba(255,255,255,0.35)", fontSize: 13, fontFamily: "var(--font-ui)", padding: "16px 0" }}>
              Loading rankings…
            </div>
          )}
        </div>
      </div>

      {/* ══════════════════════════════════════════════════════════ */}
      {/* SECTIONS 5 + 6 — SIMULATION INSIGHTS + FEATURED NATION   */}
      {/* ══════════════════════════════════════════════════════════ */}
      <div className="dashboard-main-grid" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>

        {/* SIMULATION INSIGHTS */}
        <div style={{
          background:     "rgba(10,18,34,0.72)",
          backdropFilter: "blur(16px)",
          border:         "1px solid rgba(255,255,255,0.09)",
          borderRadius:   16,
          padding:        "20px 24px",
        }}>
          <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: "0.14em", textTransform: "uppercase", color: "rgba(212,175,55,0.75)", marginBottom: 4, fontFamily: "var(--font-ui)" }}>
            SIMULATION INSIGHTS
          </div>
          <div style={{ fontSize: 18, fontWeight: 700, color: "#fff", fontFamily: "var(--font-ui)", marginBottom: 16 }}>
            Tournament intelligence
          </div>
          {[
            {
              icon:  "🏆",
              label: "Tournament Favourite",
              value: favourite?.country_name ?? "—",
              flag:  favourite ? teamFlagCode(favourite.country_uid) : undefined,
              sub:   favourite
                ? `${Math.round(((favourite.elo_rating ?? 0) / ((favourite.elo_rating ?? 0) + 100)) * 35 + 15)}% win probability`
                : "—",
              color: "#d4af37",
            },
            {
              icon:  "⚡",
              label: "Dark Horse",
              value: darkHorse?.country_name ?? "—",
              flag:  darkHorse ? teamFlagCode(darkHorse.country_uid) : undefined,
              sub:   "Strong attack, unpredictable",
              color: "#f59e0b",
            },
            {
              icon:  "🔥",
              label: "Best Attack",
              value: bestAttackAnalytics?.country_name ?? bestAttackRow?.country_name ?? "—",
              flag:  bestAttackRow ? teamFlagCode(bestAttackRow.country_uid)
                       : bestAttackAnalytics?.country_id ? teamFlagCode(bestAttackAnalytics.country_id) : undefined,
              sub:   bestAttackAnalytics
                ? `${Math.round(bestAttackAnalytics.attack ?? 0)}/100 rating`
                : "—",
              color: "#ef4444",
            },
            {
              icon:  "🛡",
              label: "Best Defence",
              value: bestDefenseAnalytics?.country_name ?? bestDefenseRow?.country_name ?? "—",
              flag:  bestDefenseRow ? teamFlagCode(bestDefenseRow.country_uid)
                       : bestDefenseAnalytics?.country_id ? teamFlagCode(bestDefenseAnalytics.country_id) : undefined,
              sub:   bestDefenseAnalytics
                ? `${Math.round(bestDefenseAnalytics.defense ?? 0)}/100 rating`
                : "—",
              color: "#3b82f6",
            },
          ].map(item => (
            <div key={item.label} style={{
              display:      "flex",
              alignItems:   "center",
              gap:          14,
              padding:      "12px 14px",
              borderRadius: 10,
              background:   "rgba(255,255,255,0.03)",
              border:       "1px solid rgba(255,255,255,0.06)",
              marginBottom: 8,
            }}>
              <span style={{ fontSize: 22, flexShrink: 0 }}>{item.icon}</span>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: "rgba(255,255,255,0.35)", fontFamily: "var(--font-ui)", marginBottom: 3 }}>
                  {item.label}
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 7 }}>
                  {item.flag && (
                    <img src={`https://flagcdn.com/w40/${item.flag}.png`} style={{ width: 18, height: 12, objectFit: "cover", borderRadius: 2 }} alt="" />
                  )}
                  <span style={{ fontSize: 15, fontWeight: 700, color: "#fff", fontFamily: "var(--font-ui)" }}>{item.value}</span>
                </div>
              </div>
              <span style={{ fontSize: 11, color: item.color, fontFamily: "var(--font-ui)", fontWeight: 500, textAlign: "right", maxWidth: 110 }}>
                {item.sub}
              </span>
            </div>
          ))}
          <a href="/tournament" style={{ display: "block", marginTop: 8, fontSize: 12, color: "rgba(212,175,55,0.7)", textDecoration: "none", fontFamily: "var(--font-ui)", textAlign: "right" }}>
            Run simulation →
          </a>
        </div>

        {/* FEATURED NATION — rotating spotlight */}
        <div style={{
          background:     "rgba(10,18,34,0.72)",
          backdropFilter: "blur(16px)",
          border:         "1px solid rgba(255,255,255,0.09)",
          borderRadius:   16,
          padding:        "20px 24px",
          display:        "flex",
          flexDirection:  "column",
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 }}>
            <div>
              <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: "0.14em", textTransform: "uppercase", color: "rgba(212,175,55,0.75)", marginBottom: 4, fontFamily: "var(--font-ui)" }}>
                FEATURED NATION
              </div>
              <div style={{ fontSize: 18, fontWeight: 700, color: "#fff", fontFamily: "var(--font-ui)" }}>
                Nation spotlight
              </div>
            </div>
            {/* Dot indicators */}
            <div style={{ display: "flex", gap: 5, alignItems: "center", marginTop: 4 }}>
              {Array.from({ length: Math.min(rankings.length, 8) }).map((_, i) => (
                <div
                  key={i}
                  onClick={() => setFeaturedNationIdx(i)}
                  style={{
                    width:        i === featuredNationIdx ? 16 : 6,
                    height:       6,
                    borderRadius: 3,
                    background:   i === featuredNationIdx ? "#d4af37" : "rgba(255,255,255,0.2)",
                    cursor:       "pointer",
                    transition:   "all 0.3s ease",
                  }}
                />
              ))}
            </div>
          </div>

          {featuredNation ? (
            <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 16 }}>
              {/* Nation hero */}
              <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
                {(() => {
                  const fc = teamFlagCode(featuredNation.country_uid);
                  return fc ? (
                    <img
                      src={`https://flagcdn.com/w160/${fc}.png`}
                      style={{ width: 72, height: 48, objectFit: "cover", borderRadius: 6, border: "1px solid rgba(255,255,255,0.15)", flexShrink: 0 }}
                      alt={featuredNation.country_name}
                    />
                  ) : (
                    <div style={{ width: 72, height: 48, borderRadius: 6, background: "rgba(255,255,255,0.06)", flexShrink: 0 }} />
                  );
                })()}
                <div>
                  <div style={{ fontFamily: "var(--font-ui)", fontSize: 26, fontWeight: 800, color: "#fff", letterSpacing: "-0.01em" }}>
                    {featuredNation.country_name}
                  </div>
                  <div style={{ fontSize: 12, color: "rgba(255,255,255,0.45)", fontFamily: "var(--font-ui)", marginTop: 2 }}>
                    {featuredNation.confederation ?? "International"} · Rank #{featuredNationIdx + 1}
                  </div>
                </div>
              </div>

              {/* Stats grid */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                {[
                  { label: "Smart Score", value: Math.round(featuredNation.elo_rating ?? 0).toLocaleString(), color: "#d4af37" },
                  { label: "Attack",      value: Math.round(featuredNation.attack_rating ?? 0).toString(),    color: "#ef4444" },
                  { label: "Defence",     value: Math.round(featuredNation.defense_rating ?? 0).toString(),   color: "#3b82f6" },
                  { label: "Form",        value: `${Math.round((featuredNation.recent_form_score ?? 0) * 100)}%`, color: "#22c55e" },
                ].map(s => (
                  <div key={s.label} style={{
                    background:   "rgba(255,255,255,0.04)",
                    border:       "1px solid rgba(255,255,255,0.07)",
                    borderRadius: 10,
                    padding:      "12px 14px",
                  }}>
                    <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: "rgba(255,255,255,0.35)", marginBottom: 4, fontFamily: "var(--font-ui)" }}>
                      {s.label}
                    </div>
                    <div style={{ fontFamily: "var(--font-display)", fontSize: 24, fontWeight: 800, color: s.color }}>
                      {s.value}
                    </div>
                  </div>
                ))}
              </div>

              {/* Actions */}
              <div style={{ display: "flex", gap: 10, marginTop: "auto" }}>
                <a
                  href="/analytics"
                  style={{
                    flex: 1, padding: "9px 0", textAlign: "center",
                    background: "rgba(212,175,55,0.12)", border: "1px solid rgba(212,175,55,0.3)",
                    borderRadius: 8, color: "#d4af37", fontFamily: "var(--font-ui)",
                    fontSize: 13, fontWeight: 600, textDecoration: "none",
                  }}
                >
                  View Analytics
                </a>
                <a
                  href="/predictions"
                  style={{
                    flex: 1, padding: "9px 0", textAlign: "center",
                    background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)",
                    borderRadius: 8, color: "rgba(255,255,255,0.7)", fontFamily: "var(--font-ui)",
                    fontSize: 13, fontWeight: 500, textDecoration: "none",
                  }}
                >
                  Match Prediction
                </a>
              </div>
            </div>
          ) : (
            <div style={{ color: "rgba(255,255,255,0.35)", fontSize: 13, fontFamily: "var(--font-ui)", padding: "16px 0" }}>
              Loading nation data…
            </div>
          )}
        </div>
      </div>

    </div>
  );
}
