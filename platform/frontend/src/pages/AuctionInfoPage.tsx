import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { API_BASE } from '@/services/api'

const TIERS = ['Elite', 'World Class', 'Quality', 'Rotation', 'Depth']
const POSITIONS = ['GK', 'DEF', 'MID', 'FWD']

const TIER_COLORS: Record<string, string> = {
  'Elite':       '#d4af37',
  'World Class': '#22c55e',
  'Quality':     '#3b82f6',
  'Rotation':    '#f59e0b',
  'Depth':       'rgba(255,255,255,0.4)',
}

const TIER_PRICES: Record<string, string> = {
  'Elite':       '1,000 coins',
  'World Class': '600 coins',
  'Quality':     '300 coins',
  'Rotation':    '150 coins',
  'Depth':       '75 coins',
}

export default function AuctionInfoPage() {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<'pool' | 'howto'>('pool')
  const [players, setPlayers] = useState<any[]>([])
  const [tierSummary, setTierSummary] = useState<Record<string, number>>({})
  const [filterTier, setFilterTier] = useState('')
  const [filterPos, setFilterPos] = useState('')
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState(0)
  const LIMIT = 20

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/auction/players/tiers/summary`)
      .then(r => r.json())
      .then(setTierSummary)
      .catch(() => {})
  }, [])

  useEffect(() => {
    setLoading(true)
    const params = new URLSearchParams()
    if (filterTier) params.set('tier', filterTier)
    if (filterPos)  params.set('position', filterPos)
    if (search)     params.set('search', search)
    params.set('limit', String(LIMIT))
    params.set('offset', String(page * LIMIT))

    fetch(`${API_BASE}/api/v1/auction/players?${params}`)
      .then(r => r.json())
      .then(d => setPlayers(d.players ?? []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [filterTier, filterPos, search, page])

  const card: React.CSSProperties = {
    background: 'rgba(10,18,34,0.72)',
    backdropFilter: 'blur(16px)',
    border: '1px solid rgba(255,255,255,0.09)',
    borderRadius: 14,
    padding: '20px 24px',
  }

  const input: React.CSSProperties = {
    background: 'rgba(255,255,255,0.05)',
    border: '1px solid rgba(255,255,255,0.12)',
    borderRadius: 8,
    padding: '9px 14px',
    color: '#fff',
    fontFamily: 'var(--font-ui)',
    fontSize: 13,
    outline: 'none',
  }

  const filterBtn = (active: boolean): React.CSSProperties => ({
    padding: '6px 14px',
    borderRadius: 20,
    border: `1px solid ${active ? '#d4af37' : 'rgba(255,255,255,0.12)'}`,
    background: active ? 'rgba(212,175,55,0.15)' : 'transparent',
    color: active ? '#d4af37' : 'rgba(255,255,255,0.55)',
    fontFamily: 'var(--font-ui)',
    fontSize: 12,
    fontWeight: 600,
    cursor: 'pointer',
    transition: 'all 0.15s',
  })

  const tab = (active: boolean): React.CSSProperties => ({
    padding: '10px 24px',
    border: 'none',
    borderBottom: `2px solid ${active ? '#d4af37' : 'transparent'}`,
    background: 'transparent',
    color: active ? '#ffffff' : 'rgba(255,255,255,0.45)',
    fontFamily: 'var(--font-ui)',
    fontSize: 14,
    fontWeight: active ? 600 : 400,
    cursor: 'pointer',
  })

  return (
    <div style={{ maxWidth: 1000, margin: '32px auto', padding: '0 20px', display: 'flex', flexDirection: 'column', gap: 16 }}>

      {/* Header */}
      <div style={card}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
          <div>
            <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'rgba(212,175,55,0.75)', marginBottom: 6 }}>
              AUCTION GUIDE
            </div>
            <div style={{ fontSize: 26, fontWeight: 700, color: '#fff', fontFamily: 'var(--font-ui)' }}>
              Player Pool & How To Play
            </div>
            <div style={{ fontSize: 14, color: 'rgba(255,255,255,0.5)', marginTop: 4 }}>
              Browse all {Object.values(tierSummary).reduce((a,b) => a+b, 0).toLocaleString()} players available in the auction
            </div>
          </div>
          <button
            onClick={() => navigate(-1)}
            style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 8, padding: '8px 16px', color: '#fff', fontFamily: 'var(--font-ui)', fontSize: 13, cursor: 'pointer' }}
          >
            ← Back
          </button>
        </div>

        {/* Tabs */}
        <div style={{ display: 'flex', borderBottom: '1px solid rgba(255,255,255,0.08)', marginTop: 20 }}>
          <button style={tab(activeTab === 'pool')} onClick={() => setActiveTab('pool')}>🏟 Player Pool</button>
          <button style={tab(activeTab === 'howto')} onClick={() => setActiveTab('howto')}>📖 How To Play</button>
        </div>
      </div>

      {/* ── TAB: PLAYER POOL ── */}
      {activeTab === 'pool' && (
        <>
          {/* Tier summary */}
          <div className="info-tiers-grid">
            {TIERS.map(tier => (
              <div
                key={tier}
                onClick={() => setFilterTier(filterTier === tier ? '' : tier)}
                style={{
                  ...card,
                  padding: '14px 16px',
                  cursor: 'pointer',
                  border: `1px solid ${filterTier === tier ? TIER_COLORS[tier] : 'rgba(255,255,255,0.09)'}`,
                  transition: 'border-color 0.15s',
                }}
              >
                <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase', color: TIER_COLORS[tier], marginBottom: 4 }}>
                  {tier}
                </div>
                <div style={{ fontFamily: 'var(--font-display)', fontSize: 26, fontWeight: 700, color: '#fff' }}>
                  {(tierSummary[tier] ?? 0).toLocaleString()}
                </div>
                <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.35)', marginTop: 2 }}>
                  From {TIER_PRICES[tier]}
                </div>
              </div>
            ))}
          </div>

          {/* Filters */}
          <div style={{ ...card, padding: '14px 20px' }}>
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
              <input
                style={{ ...input, flex: 1, minWidth: 200 }}
                placeholder='Search player name...'
                value={search}
                onChange={e => { setSearch(e.target.value); setPage(0) }}
              />
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                {POSITIONS.map(pos => (
                  <button
                    key={pos}
                    style={filterBtn(filterPos === pos)}
                    onClick={() => { setFilterPos(filterPos === pos ? '' : pos); setPage(0) }}
                  >
                    {pos}
                  </button>
                ))}
                <div style={{ width: 1, background: 'rgba(255,255,255,0.1)', margin: '0 4px' }} />
                {TIERS.map(t => (
                  <button
                    key={t}
                    style={filterBtn(filterTier === t)}
                    onClick={() => { setFilterTier(filterTier === t ? '' : t); setPage(0) }}
                  >
                    {t}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Player table */}
          <div style={{ ...card, overflow: 'hidden' }}>
            {loading ? (
              <div style={{ textAlign: 'center', padding: 32, color: 'rgba(255,255,255,0.35)', fontSize: 14 }}>Loading players...</div>
            ) : (
              <>
                <div className="wc-table-shell">
                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
                      {['Player', 'Position', 'Club', 'Nation', 'Market Value', 'Base Price', 'Tier'].map(h => (
                        <th key={h} style={{ padding: '8px 12px', textAlign: 'left', fontSize: 10, fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.35)' }}>
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {players.map((p, i) => (
                      <tr
                        key={p.id}
                        style={{ borderBottom: '1px solid rgba(255,255,255,0.04)', background: i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.01)' }}
                      >
                        <td style={{ padding: '10px 12px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            {p.image_url && (
                              <img src={p.image_url} alt='' style={{ width: 28, height: 28, borderRadius: '50%', objectFit: 'cover', flexShrink: 0 }} />
                            )}
                            <span style={{ fontSize: 13, fontWeight: 600, color: '#fff', fontFamily: 'var(--font-ui)' }}>{p.name}</span>
                          </div>
                        </td>
                        <td style={{ padding: '10px 12px' }}>
                          <span style={{ fontSize: 11, fontWeight: 700, padding: '3px 8px', borderRadius: 4, background: 'rgba(255,255,255,0.07)', color: 'rgba(255,255,255,0.7)' }}>
                            {p.position}
                          </span>
                        </td>
                        <td style={{ padding: '10px 12px', fontSize: 13, color: 'rgba(255,255,255,0.6)' }}>{p.club}</td>
                        <td style={{ padding: '10px 12px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                            <img src={`https://flagcdn.com/w40/${p.flag_code}.png`} style={{ width: 18, height: 12, objectFit: 'cover', borderRadius: 2 }} alt='' />
                            <span style={{ fontSize: 12, color: 'rgba(255,255,255,0.55)' }}>{p.iso_code}</span>
                          </div>
                        </td>
                        <td style={{ padding: '10px 12px', fontFamily: 'var(--font-display)', fontSize: 14, fontWeight: 600, color: '#fff' }}>
                          €{p.market_value >= 1_000_000 ? `${(p.market_value/1_000_000).toFixed(0)}M` : `${(p.market_value/1_000).toFixed(0)}K`}
                        </td>
                        <td style={{ padding: '10px 12px', fontFamily: 'var(--font-display)', fontSize: 14, fontWeight: 700, color: '#d4af37' }}>
                          {p.base_price?.toLocaleString()}
                        </td>
                        <td style={{ padding: '10px 12px' }}>
                          <span style={{ fontSize: 11, fontWeight: 700, padding: '3px 8px', borderRadius: 4, color: TIER_COLORS[p.tier], background: `${TIER_COLORS[p.tier]}18` }}>
                            {p.tier}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                </div>

                {/* Pagination */}
                <div style={{ display: 'flex', justifyContent: 'center', gap: 10, marginTop: 16 }}>
                  <button
                    disabled={page === 0}
                    onClick={() => setPage(p => p - 1)}
                    style={{ padding: '7px 16px', background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 7, color: page === 0 ? 'rgba(255,255,255,0.2)' : '#fff', cursor: page === 0 ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-ui)', fontSize: 13 }}
                  >
                    ← Prev
                  </button>
                  <span style={{ padding: '7px 12px', fontSize: 13, color: 'rgba(255,255,255,0.45)' }}>
                    Page {page + 1}
                  </span>
                  <button
                    disabled={players.length < LIMIT}
                    onClick={() => setPage(p => p + 1)}
                    style={{ padding: '7px 16px', background: players.length < LIMIT ? 'transparent' : '#d4af37', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 7, color: players.length < LIMIT ? 'rgba(255,255,255,0.2)' : '#0a0f1a', cursor: players.length < LIMIT ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-ui)', fontSize: 13, fontWeight: 600 }}
                  >
                    Next →
                  </button>
                </div>
              </>
            )}
          </div>
        </>
      )}

      {/* ── TAB: HOW TO PLAY ── */}
      {activeTab === 'howto' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

          {[
            {
              step: '1',
              title: 'Create or Join a League',
              body: 'One manager creates a league and shares the invite code. Others join using the code. Each manager is allocated a standard budget of 50,000 coins to bid on players.',
              icon: '🏟',
            },
            {
              step: '2',
              title: 'The Auction Begins',
              body: 'When the host clicks "Start Auction", the system automatically nominates players one by one, descending through Elite, World Class, Quality, Rotation, and Depth tiers.',
              icon: '🎯',
            },
            {
              step: '3',
              title: 'Bidding & Bidding Timers',
              body: 'When a player is nominated, managers have 60 seconds to place an opening bid at the base price. Once a bid is placed, a 30-second countdown triggers. Every subsequent bid resets this countdown to 30 seconds. If the timer hits zero, the player is sold to the highest bidder.',
              icon: '💰',
            },
            {
              step: '4',
              title: 'Host Control: Skip & Stop',
              body: 'The league host has full administrative control to keep the pace smooth:\n• Skip Player: If no bids are placed on the current player, the host can skip them to nominate the next player immediately.\n• Stop Auction: The host can terminate the auction at any point, marking the league as active and moving to the main dashboard.',
              icon: '⚡',
            },
            {
              step: '5',
              title: 'Leave & Rejoin Seamlessly',
              body: 'Any manager can leave the room at any time. When you rejoin using your registered username and invite code, you will resume exactly from the auction\'s current global status. Any players nominated or sold while you were away are automatically synchronized, ensuring zero delays.',
              icon: '🚪',
            },
            {
              step: '6',
              title: 'Squad & Positional Rules',
              body: `You must build a squad of 15 players matching both minimum and maximum limits:\n• Goalkeepers (GK): Min 2 · Max 3\n• Defenders (DEF): Min 5 · Max 6\n• Midfielders (MID): Min 5 · Max 6\n• Forwards (FWD): Min 3 · Max 5\n\nYou cannot place a bid that would violate these position constraints or exceed the 15-player squad limit.`,
              icon: '📋',
            },
            {
              step: '7',
              title: 'Scoring During the World Cup',
              body: `Points are awarded after each real WC match:\n• Goal (FWD/MID): +5 pts · Goal (DEF): +6 pts · Goal (GK): +6 pts\n• Assist: +3 pts\n• Clean sheet (DEF/GK, 60+ mins): +4 pts\n• Clean sheet (MID, 60+ mins): +1 pt\n• 90 mins played: +2 pts · 60+ mins played: +1 pt\n• Yellow card: −1 pt · Red card: −3 pts\n• GK: +1 pt per 3 saves`,
              icon: '⚽',
            },
            {
              step: '8',
              title: 'Champion & Leaderboard',
              body: 'The leaderboard updates automatically after each match. Your cumulative points across the entire World Cup will decide your rank. The manager with the highest score when the tournament ends is crowned champion.',
              icon: '🏆',
            },
          ].map(item => (
            <div key={item.step} style={{ ...card, display: 'flex', gap: 18 }}>
              <div style={{
                width: 44, height: 44, borderRadius: '50%',
                background: 'rgba(212,175,55,0.12)',
                border: '1px solid rgba(212,175,55,0.25)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 20, flexShrink: 0,
              }}>
                {item.icon}
              </div>
              <div>
                <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'rgba(212,175,55,0.7)', marginBottom: 4 }}>
                  STEP {item.step}
                </div>
                <div style={{ fontSize: 16, fontWeight: 700, color: '#fff', fontFamily: 'var(--font-ui)', marginBottom: 6 }}>
                  {item.title}
                </div>
                <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.6)', fontFamily: 'var(--font-ui)', lineHeight: 1.7, whiteSpace: 'pre-line' }}>
                  {item.body}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

    </div>
  )
}
