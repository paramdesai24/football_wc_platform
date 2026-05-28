import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

const API = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export default function AuctionPage() {
  const navigate = useNavigate()

  // Create league state
  const [createForm, setCreateForm] = useState({
    name: '', host_id: '', display_name: '', budget: 5000, squad_size: 15
  })
  const [inviteCode, setInviteCode] = useState('')
  const [createdLeagueId, setCreatedLeagueId] = useState('')
  const [createLoading, setCreateLoading] = useState(false)
  const [createError, setCreateError] = useState('')

  // Join league state
  const [joinForm, setJoinForm] = useState({
    invite_code: '', user_id: '', username: '', team_name: ''
  })
  const [joinLoading, setJoinLoading] = useState(false)
  const [joinError, setJoinError] = useState('')

  async function handleCreate() {
    setCreateLoading(true); setCreateError('')
    try {
      const res = await fetch(`${API}/api/v1/leagues/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(createForm)
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail ?? 'Failed to create')
      setInviteCode(data.invite_code)
      setCreatedLeagueId(data.league_id)
    } catch (e: any) { setCreateError(e.message) }
    finally { setCreateLoading(false) }
  }

  async function handleJoin() {
    setJoinLoading(true); setJoinError('')
    try {
      const res = await fetch(`${API}/api/v1/leagues/${joinForm.invite_code}/join`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: joinForm.user_id, team_name: joinForm.team_name })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail ?? 'Failed to join')
      navigate(
        `/auction/room/${data.league_id}` +
        `?userId=${joinForm.user_id}` +
        `&username=${encodeURIComponent(joinForm.username || joinForm.user_id)}`
      )
    } catch (e: any) { setJoinError(e.message) }
    finally { setJoinLoading(false) }
  }

  const card: React.CSSProperties = {
    background: 'rgba(10,18,34,0.72)', backdropFilter: 'blur(16px)',
    border: '1px solid rgba(255,255,255,0.09)', borderRadius: 14,
    padding: '28px 32px', display: 'flex', flexDirection: 'column', gap: 16,
  }
  const input: React.CSSProperties = {
    background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.12)',
    borderRadius: 8, padding: '10px 14px', color: '#fff',
    fontFamily: 'var(--font-ui)', fontSize: 14, outline: 'none', width: '100%',
  }
  const label: React.CSSProperties = {
    fontSize: 11, fontWeight: 600, letterSpacing: '0.1em',
    textTransform: 'uppercase', color: 'rgba(255,255,255,0.4)',
    fontFamily: 'var(--font-ui)',
  }
  const btn: React.CSSProperties = {
    padding: '11px 0', background: '#d4af37', border: 'none',
    borderRadius: 8, color: '#0a0f1a', fontFamily: 'var(--font-ui)',
    fontSize: 14, fontWeight: 700, cursor: 'pointer', width: '100%',
  }

  return (
    <div style={{ maxWidth: 960, margin: '40px auto', padding: '0 24px' }}>
      <div style={{ marginBottom: 32 }}>
        <div style={{ fontSize: 11, fontWeight: 600, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'rgba(212,175,55,0.75)', marginBottom: 8 }}>AUCTION CENTER</div>
        <div style={{ fontSize: 32, fontWeight: 700, color: '#fff', fontFamily: 'var(--font-ui)' }}>Build your squad</div>
        <div style={{ fontSize: 15, color: 'rgba(255,255,255,0.5)', marginTop: 6 }}>Create a private league or join one with an invite code.</div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>

        {/* CREATE */}
        <div style={card}>
          <div style={{ fontSize: 16, fontWeight: 700, color: '#fff' }}>Create League</div>
          <div><div style={label}>League Name</div><input style={input} placeholder='My League' value={createForm.name} onChange={e => setCreateForm(f => ({...f, name: e.target.value}))} /></div>
          <div><div style={label}>Your Username</div><input style={input} placeholder='yourname' value={createForm.host_id} onChange={e => setCreateForm(f => ({...f, host_id: e.target.value}))} /></div>
          <div><div style={label}>Your Display Name</div><input style={input} placeholder='Your Name' value={createForm.display_name} onChange={e => setCreateForm(f => ({...f, display_name: e.target.value}))} /></div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div><div style={label}>Budget (coins)</div><input style={input} type='number' value={createForm.budget} onChange={e => setCreateForm(f => ({...f, budget: +e.target.value}))} /></div>
            <div><div style={label}>Squad Size</div><input style={input} type='number' value={createForm.squad_size} onChange={e => setCreateForm(f => ({...f, squad_size: +e.target.value}))} /></div>
          </div>
          {createError && <div style={{ color: '#f87171', fontSize: 13 }}>{createError}</div>}
          {!inviteCode
            ? <button style={btn} onClick={handleCreate} disabled={createLoading}>{createLoading ? 'Creating...' : 'Create League'}</button>
            : <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div style={{ background: 'rgba(212,175,55,0.1)', border: '1px solid rgba(212,175,55,0.3)', borderRadius: 8, padding: '12px 16px', textAlign: 'center' }}>
                  <div style={{ fontSize: 11, color: 'rgba(212,175,55,0.7)', marginBottom: 4 }}>INVITE CODE</div>
                  <div style={{ fontFamily: 'var(--font-display)', fontSize: 28, fontWeight: 800, color: '#d4af37', letterSpacing: '0.1em' }}>{inviteCode}</div>
                  <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', marginTop: 4 }}>Share this with friends</div>
                </div>
                <button style={btn} onClick={() => navigate(
                  `/auction/room/${createdLeagueId}` +
                  `?userId=${createForm.host_id}` +
                  `&username=${encodeURIComponent(createForm.display_name || createForm.host_id)}`
                )}>Enter Auction Room →</button>
              </div>
          }
        </div>

        {/* JOIN */}
        <div style={card}>
          <div style={{ fontSize: 16, fontWeight: 700, color: '#fff' }}>Join League</div>
          <div><div style={label}>Invite Code</div><input style={input} placeholder='WOLF-7742' value={joinForm.invite_code} onChange={e => setJoinForm(f => ({...f, invite_code: e.target.value.toUpperCase()}))} /></div>
          <div><div style={label}>Your Username</div><input style={input} placeholder='yourname' value={joinForm.user_id} onChange={e => setJoinForm(f => ({...f, user_id: e.target.value}))} /></div>
          <div><div style={label}>Display Name</div><input style={input} placeholder='Your Name' value={joinForm.username} onChange={e => setJoinForm(f => ({...f, username: e.target.value}))} /></div>
          <div><div style={label}>Team Name</div><input style={input} placeholder='My Dream Team' value={joinForm.team_name} onChange={e => setJoinForm(f => ({...f, team_name: e.target.value}))} /></div>
          {joinError && <div style={{ color: '#f87171', fontSize: 13 }}>{joinError}</div>}
          <button style={{...btn, marginTop: 'auto'}} onClick={handleJoin} disabled={joinLoading}>{joinLoading ? 'Joining...' : 'Join League'}</button>
        </div>

      </div>
    </div>
  )
}