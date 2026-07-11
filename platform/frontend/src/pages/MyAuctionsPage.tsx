import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import useAuthStore from '@/store/authStore'
import { API_BASE } from '@/services/api'

export default function MyAuctionsPage() {
  const { user }     = useAuthStore()
  const navigate     = useNavigate()
  const userEmail    = user?.email ?? ''
  const displayName  = user?.username ?? userEmail.split('@')[0] ?? ''

  const [leagues,        setLeagues]        = useState<any[]>([])
  const [selectedLeague, setSelectedLeague] = useState<any>(null)
  const [squad,          setSquad]          = useState<any[]>([])
  const [leagueDetail,   setLeagueDetail]   = useState<any>(null)
  const [loadingLeagues, setLoadingLeagues] = useState(true)
  const [loadingSquad,   setLoadingSquad]   = useState(false)

  // ── Fetch all leagues this email is in ──────────────────────────────────────
  useEffect(() => {
    if (!userEmail) return
    setLoadingLeagues(true)
    fetch(`${API_BASE}/api/v1/leagues/my?user_id=${encodeURIComponent(userEmail)}`)
      .then(r => r.json())
      .then(d => setLeagues(d.leagues ?? []))
      .catch(() => setLeagues([]))
      .finally(() => setLoadingLeagues(false))
  }, [userEmail])

  // ── Fetch squad + detail when a league is selected ─────────────────────────
  useEffect(() => {
    if (!selectedLeague) return
    setLoadingSquad(true)
    Promise.all([
      fetch(`${API_BASE}/api/v1/leagues/${selectedLeague.id}`).then(r => r.json()),
      fetch(`${API_BASE}/api/v1/leagues/${selectedLeague.id}/squad/${encodeURIComponent(userEmail)}`).then(r => r.json()),
    ]).then(([detail, squadData]) => {
      setLeagueDetail(detail)
      setSquad(squadData.squad ?? [])
    }).catch(() => {})
    .finally(() => setLoadingSquad(false))
  }, [selectedLeague, userEmail])

  const card: React.CSSProperties = {
    background: 'rgba(10,18,34,0.72)',
    backdropFilter: 'blur(16px)',
    border: '1px solid rgba(255,255,255,0.09)',
    borderRadius: 14,
    padding: '16px 20px',
  }

  const forfeitedBannerStyle: React.CSSProperties = {
    background: 'rgba(239, 68, 68, 0.05)',
    backdropFilter: 'blur(12px)',
    border: '1px solid rgba(239, 68, 68, 0.35)',
    borderRadius: 14,
    padding: '16px 20px',
    display: 'flex',
    alignItems: 'center',
    gap: 14,
    color: '#f87171',
    fontFamily: 'var(--font-ui)',
    boxShadow: '0 8px 32px rgba(0,0,0,0.15)',
  }

  const disqualifiedBannerStyle: React.CSSProperties = {
    background: 'rgba(239, 68, 68, 0.08)',
    backdropFilter: 'blur(12px)',
    border: '1px solid rgba(239, 68, 68, 0.45)',
    borderRadius: 14,
    padding: '16px 20px',
    display: 'flex',
    alignItems: 'center',
    gap: 14,
    color: '#f87171',
    fontFamily: 'var(--font-ui)',
    boxShadow: '0 8px 32px rgba(0,0,0,0.15)',
  }

  // ── Group squad by position ────────────────────────────────────────────────
  const byPos: Record<string, any[]> = { GK: [], DEF: [], MID: [], FWD: [] }
  squad.forEach(s => {
    const pos = s.player?.position
    if (pos && byPos[pos]) {
      byPos[pos].push(s)
    }
  })

  const totalPoints = leagueDetail?.members?.find((m: any) => m.user_id === userEmail)?.total_points ?? 0

  return (
    <div style={{ maxWidth: 900, margin: '32px auto', padding: '0 20px', display: 'flex', flexDirection: 'column', gap: 16 }}>

      {/* ── Header ── */}
      <div style={card}>
        <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'rgba(212,175,55,0.75)', marginBottom: 6, fontFamily: 'var(--font-ui)' }}>
          MY AUCTIONS
        </div>
        <div style={{ fontSize: 24, fontWeight: 700, color: '#fff', fontFamily: 'var(--font-ui)' }}>
          {displayName}'s leagues
        </div>
        <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.4)', marginTop: 4, fontFamily: 'var(--font-ui)' }}>
          {userEmail}
        </div>
      </div>

      {!selectedLeague ? (
        // ── LEAGUE LIST VIEW ─────────────────────────────────────────────────
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {loadingLeagues && (
            <div style={{ ...card, textAlign: 'center', color: 'rgba(255,255,255,0.35)', fontSize: 14 }}>
              Loading your leagues...
            </div>
          )}
          {!loadingLeagues && leagues.length === 0 && (
            <div style={{ ...card, textAlign: 'center', padding: '48px 24px' }}>
              <div style={{ fontSize: 36, marginBottom: 12 }}>🏟</div>
              <div style={{ fontSize: 16, fontWeight: 600, color: '#fff', marginBottom: 6 }}>No leagues yet</div>
              <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.4)', marginBottom: 20 }}>
                Create or join a league to get started
              </div>
              <button
                id="btn-go-to-auction"
                onClick={() => navigate('/auction')}
                style={{ padding: '10px 24px', background: '#d4af37', border: 'none', borderRadius: 8, color: '#0a0f1a', fontFamily: 'var(--font-ui)', fontSize: 14, fontWeight: 700, cursor: 'pointer' }}
              >
                Go to Auction →
              </button>
            </div>
          )}
          {leagues.map(league => (
            <div
              key={league.id}
              id={`league-row-${league.id}`}
              onClick={() => setSelectedLeague(league)}
              style={{
                ...card,
                cursor:     'pointer',
                display:    'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap:        16,
                transition: 'border-color 0.15s',
                flexWrap:   'wrap',
              }}
              onMouseEnter={e => (e.currentTarget as HTMLDivElement).style.borderColor = 'rgba(212,175,55,0.35)'}
              onMouseLeave={e => (e.currentTarget as HTMLDivElement).style.borderColor = 'rgba(255,255,255,0.09)'}
            >
              <div style={{ flex: '1 1 180px', minWidth: 180 }}>
                <div style={{ fontSize: 16, fontWeight: 700, color: '#fff', fontFamily: 'var(--font-ui)', marginBottom: 4, display: 'flex', alignItems: 'center', gap: 6 }}>
                  {league.name}
                  {(league.status === 'forfeited' || league.my_is_disqualified) && (
                    <span title={league.my_is_disqualified ? "You are disqualified" : "League Forfeited"} style={{ fontSize: 13 }}>⚠️</span>
                  )}
                </div>
                <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                  <span style={{ fontSize: 12, color: 'rgba(255,255,255,0.4)', fontFamily: 'var(--font-ui)' }}>
                    Code: <span style={{ color: '#d4af37', fontFamily: 'var(--font-display)', fontWeight: 700 }}>{league.invite_code}</span>
                  </span>
                  <span style={{
                    fontSize: 11, fontWeight: 600, padding: '2px 8px', borderRadius: 20,
                    background: league.my_is_disqualified ? 'rgba(239,68,68,0.2)' : league.status === 'forfeited' ? 'rgba(239,68,68,0.15)' : league.status === 'active' ? 'rgba(34,197,94,0.15)' : 'rgba(212,175,55,0.12)',
                    color:      league.my_is_disqualified ? '#ef4444' : league.status === 'forfeited' ? '#f87171' : league.status === 'active' ? '#22c55e' : '#d4af37',
                    fontFamily: 'var(--font-ui)',
                  }}>
                    {league.my_is_disqualified ? 'DISQUALIFIED' : league.status?.toUpperCase()}
                  </span>
                </div>
              </div>
              <div style={{ textAlign: 'left', flex: '1 0 auto', display: 'flex', flexDirection: 'column', alignItems: 'flex-start', minWidth: 100 }}>
                <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.35)', fontFamily: 'var(--font-ui)', marginBottom: 2 }}>
                  Budget left
                </div>
                <div style={{ fontFamily: 'var(--font-display)', fontSize: 18, fontWeight: 700, color: '#d4af37' }}>
                  {(league.my_budget_left ?? 0).toLocaleString()}
                </div>
              </div>
              <span style={{ color: 'rgba(255,255,255,0.2)', fontSize: 20, marginLeft: 'auto' }}>›</span>
            </div>
          ))}
        </div>
      ) : (
        // ── SQUAD DETAIL VIEW ────────────────────────────────────────────────
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

          {selectedLeague.my_is_disqualified && (
            <div style={disqualifiedBannerStyle}>
              <span style={{ fontSize: 22, filter: 'drop-shadow(0 0 4px rgba(239,68,68,0.3))' }}>❌</span>
              <div>
                <h3 style={{ margin: "0 0 4px 0", fontSize: 14, fontWeight: 700, color: "#f87171", fontFamily: "var(--font-display)" }}>You Are Disqualified</h3>
                <p style={{ margin: 0, fontSize: 13, opacity: 0.8, lineHeight: 1.5 }}>
                  You have been disqualified from this league because your roster did not satisfy the squad size or position balance requirements when the auction ended.
                </p>
              </div>
            </div>
          )}

          {selectedLeague.status === 'forfeited' && (
            <div style={forfeitedBannerStyle}>
              <span style={{ fontSize: 22, filter: 'drop-shadow(0 0 4px rgba(239,68,68,0.3))' }}>⚠️</span>
              <div>
                <h3 style={{ margin: "0 0 4px 0", fontSize: 14, fontWeight: 700, color: "#f87171", fontFamily: "var(--font-display)" }}>League Forfeited</h3>
                <p style={{ margin: 0, fontSize: 13, opacity: 0.8, lineHeight: 1.5 }}>
                  This league has been forfeited because no participant met the minimum roster position and size requirements.
                </p>
              </div>
            </div>
          )}

          {/* Back + header */}
          <div style={card}>
            <button
              id="btn-back-to-leagues"
              onClick={() => { setSelectedLeague(null); setSquad([]); setLeagueDetail(null) }}
              style={{ background: 'none', border: 'none', color: 'rgba(255,255,255,0.45)', fontFamily: 'var(--font-ui)', fontSize: 13, cursor: 'pointer', padding: '0 0 12px 0', display: 'block' }}
            >
              ← All leagues
            </button>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
              <div>
                <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'rgba(212,175,55,0.75)', marginBottom: 4, fontFamily: 'var(--font-ui)' }}>
                  {selectedLeague.name}
                </div>
                <div style={{ fontSize: 22, fontWeight: 700, color: '#fff', fontFamily: 'var(--font-ui)' }}>
                  {displayName}'s squad
                </div>
              </div>
              <div style={{ display: 'flex', gap: 20 }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontFamily: 'var(--font-display)', fontSize: 28, fontWeight: 800, color: '#d4af37' }}>{totalPoints}</div>
                  <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.35)', fontFamily: 'var(--font-ui)', letterSpacing: '0.08em' }}>POINTS</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontFamily: 'var(--font-display)', fontSize: 28, fontWeight: 800, color: '#fff' }}>{squad.length}</div>
                  <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.35)', fontFamily: 'var(--font-ui)', letterSpacing: '0.08em' }}>PLAYERS</div>
                </div>
              </div>
            </div>
            <button
              id="btn-view-leaderboard"
              onClick={() => navigate(`/league/${selectedLeague.id}/leaderboard`)}
              style={{ marginTop: 14, padding: '9px 18px', background: 'rgba(212,175,55,0.1)', border: '1px solid rgba(212,175,55,0.25)', borderRadius: 8, color: '#d4af37', fontFamily: 'var(--font-ui)', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}
            >
              View League Leaderboard →
            </button>
          </div>

          {loadingSquad && (
            <div style={{ ...card, textAlign: 'center', color: 'rgba(255,255,255,0.35)', fontSize: 14 }}>
              Loading squad...
            </div>
          )}

          {/* Squad by position */}
          {!loadingSquad && ['GK', 'DEF', 'MID', 'FWD'].map(pos => {
            const players = byPos[pos]
            if (!players || players.length === 0) return null
            const posLabel = pos === 'GK' ? 'GOALKEEPERS' : pos === 'DEF' ? 'DEFENDERS' : pos === 'MID' ? 'MIDFIELDERS' : 'FORWARDS'
            return (
              <div key={pos} style={card}>
                <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'rgba(212,175,55,0.75)', marginBottom: 14, fontFamily: 'var(--font-ui)' }}>
                  {posLabel} · {players.length}
                </div>
                {players.map((s: any, i: number) => {
                  const p = s.player
                  return (
                    <div key={i} style={{
                      display: 'flex', alignItems: 'center', gap: 12,
                      padding: '10px 0',
                      borderBottom: i < players.length - 1 ? '1px solid rgba(255,255,255,0.05)' : 'none',
                    }}>
                      {p?.image_url && (
                        <img
                          src={p.image_url}
                          style={{ width: 36, height: 36, borderRadius: '50%', objectFit: 'cover', flexShrink: 0, border: '1px solid rgba(255,255,255,0.1)' }}
                          alt=""
                        />
                      )}
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                          {p?.flag_code && (
                            <img
                              src={`https://flagcdn.com/w40/${p.flag_code}.png`}
                              style={{ width: 16, height: 11, objectFit: 'cover', borderRadius: 2 }}
                              alt=""
                            />
                          )}
                          <span style={{ fontSize: 14, fontWeight: 600, color: '#fff', fontFamily: 'var(--font-ui)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {p?.name ?? s.player_id}
                          </span>
                        </div>
                        <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', fontFamily: 'var(--font-ui)' }}>
                          {p?.club}
                        </span>
                      </div>
                      <div style={{ textAlign: 'right', flexShrink: 0 }}>
                        <div style={{ fontFamily: 'var(--font-display)', fontSize: 14, fontWeight: 700, color: '#a78bfa' }}>
                          {s.player_total_points ?? 0} pts
                        </div>
                        <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.35)', fontFamily: 'var(--font-ui)' }}>
                          points
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
