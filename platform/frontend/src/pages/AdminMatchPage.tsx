import { useEffect, useState } from "react";
import { API_BASE } from "@/services/api";
import { toast } from "@/store/toastStore";
import { EmptyState } from "@/components/ui/EmptyState";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";

type PerfRow = {
  player_id?: string;
  name?: string;
  goals?: number;
  assists?: number;
  minutes_played?: number;
  yellow_cards?: number;
  red_cards?: number;
  clean_sheet?: boolean;
  saves?: number;
};

export default function AdminMatchPage() {
  const [matchId, setMatchId] = useState("");
  const [stage, setStage] = useState("GROUP");
  const [homeCode, setHomeCode] = useState("");
  const [awayCode, setAwayCode] = useState("");
  const [homeScore, setHomeScore] = useState<number | "">("");
  const [awayScore, setAwayScore] = useState<number | "">("");

  const [rows, setRows] = useState<PerfRow[]>([]);
  const [search, setSearch] = useState("");
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [showRecalcConfirm, setShowRecalcConfirm] = useState(false);

  const pageStyle: React.CSSProperties = {
    maxWidth: 860,
    margin: '32px auto',
    padding: '0 20px',
    display: 'flex',
    flexDirection: 'column',
    gap: 16,
  };

  const card: React.CSSProperties = {
    background: 'rgba(10,18,34,0.72)',
    backdropFilter: 'blur(16px)',
    border: '1px solid rgba(255,255,255,0.09)',
    borderRadius: 14,
    padding: '20px 24px',
    display: 'flex',
    flexDirection: 'column',
    gap: 14,
  };

  const eyebrow: React.CSSProperties = {
    fontSize: 10,
    fontWeight: 600,
    letterSpacing: '0.14em',
    textTransform: 'uppercase' as const,
    color: 'rgba(212,175,55,0.8)',
    fontFamily: 'var(--font-ui)',
  };

  const sectionTitle: React.CSSProperties = {
    fontSize: 20,
    fontWeight: 700,
    color: '#ffffff',
    fontFamily: 'var(--font-ui)',
    letterSpacing: '-0.01em',
  };

  const fieldLabel: React.CSSProperties = {
    fontSize: 11,
    fontWeight: 500,
    letterSpacing: '0.08em',
    textTransform: 'uppercase' as const,
    color: 'rgba(255,255,255,0.4)',
    fontFamily: 'var(--font-ui)',
    marginBottom: 5,
    display: 'block',
  };

  const inputStyle: React.CSSProperties = {
    width: '100%',
    background: 'rgba(255,255,255,0.05)',
    border: '1px solid rgba(255,255,255,0.12)',
    borderRadius: 8,
    padding: '10px 14px',
    color: '#ffffff',
    fontFamily: 'var(--font-ui)',
    fontSize: 14,
    outline: 'none',
  };

  const selectStyle: React.CSSProperties = {
    ...inputStyle,
    cursor: 'pointer',
  };

  const primaryBtn: React.CSSProperties = {
    padding: '11px 28px',
    background: '#d4af37',
    border: 'none',
    borderRadius: 8,
    color: '#0a0f1a',
    fontFamily: 'var(--font-ui)',
    fontSize: 14,
    fontWeight: 700,
    cursor: 'pointer',
  };

  const ghostBtn: React.CSSProperties = {
    padding: '9px 18px',
    background: 'rgba(255,255,255,0.06)',
    border: '1px solid rgba(255,255,255,0.12)',
    borderRadius: 8,
    color: '#ffffff',
    fontFamily: 'var(--font-ui)',
    fontSize: 13,
    fontWeight: 500,
    cursor: 'pointer',
  };

  const dangerBtn: React.CSSProperties = {
    padding: '6px 12px',
    background: 'rgba(239,68,68,0.15)',
    border: '1px solid rgba(239,68,68,0.3)',
    borderRadius: 6,
    color: '#f87171',
    fontFamily: 'var(--font-ui)',
    fontSize: 12,
    fontWeight: 500,
    cursor: 'pointer',
  };

  function addRow() {
    setRows((r) => [...r, {}]);
  }

  function updateRow(idx: number, patch: Partial<PerfRow>) {
    setRows((r) => r.map((row, i) => (i === idx ? { ...row, ...patch } : row)));
  }

  function removeRow(idx: number) {
    setRows((r) => r.filter((_, i) => i !== idx));
  }

  async function handleSubmit() {
    setLoading(true);
    setError("");
    setSuccess("");
    try {
      const body = {
        match_id: matchId.trim(),
        stage,
        home_code: homeCode.trim().toUpperCase(),
        away_code: awayCode.trim().toUpperCase(),
        home_score: homeScore === "" ? 0 : Number(homeScore),
        away_score: awayScore === "" ? 0 : Number(awayScore),
        performances: rows.map((r) => ({
          player_id: r.player_id,
          goals: Number(r.goals ?? 0),
          assists: Number(r.assists ?? 0),
          minutes_played: Number(r.minutes_played ?? 0),
          yellow_cards: Number(r.yellow_cards ?? 0),
          red_cards: Number(r.red_cards ?? 0),
          clean_sheet: Boolean(r.clean_sheet ?? false),
          saves: Number(r.saves ?? 0),
        })),
      };

      console.log('Submitting match result:', body);

      const res = await fetch(`${API_BASE}/api/v1/admin/matches/result`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      console.log('Match result response:', data);

      if (!res.ok) {
        if (data.detail && typeof data.detail === 'object' && data.detail.invalid_players) {
          const msgs = data.detail.invalid_players as string[];
          setError(`❌ ${data.detail.error}: ${msgs.join(' · ')}`);
        } else {
          setError(data.detail ?? data.message ?? `Error ${res.status}`);
        }
        return;
      }

      toast.success(`Match ${data.match_id} processed successfully for all leagues`);
      setSuccess(`✅ Match ${data.match_id} processed successfully for all leagues`);
      setRows([]);
      setMatchId("");
      setHomeCode("");
      setAwayCode("");
      setHomeScore(0);
      setAwayScore(0);
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : "Network error — is the backend running?";
      toast.error(message);
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  async function handleRecalculate() {
    setLoading(true);
    setError("");
    setSuccess("");
    try {
      const res = await fetch(`${API_BASE}/api/v1/admin/matches/recalculate`, { method: "POST" });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail ?? data.message ?? `Error ${res.status}`);
        return;
      }
      toast.success(`Recalculated points from ${data.count} matches`);
      setSuccess(`✅ Recalculated points from ${data.count} matches`);
    } catch {
      toast.error('Recalculation failed');
      setError('Recalculation failed');
    } finally {
      setLoading(false);
    }
  }

  async function handleScrape() {
    setLoading(true)
    setError('')
    setSuccess('')
    try {
      const res = await fetch(`${API_BASE}/api/v1/admin/matches/scrape`, { method: 'POST' })
      const data = await res.json()
      if (!res.ok) {
        setError(data.detail ?? data.message ?? 'Scrape failed')
        return
      }
      const processed = (data.results ?? []).filter((r: any) => r.status === 'processed').length
      toast.success(`Scraped ${data.scraped} matches — ${processed} new matches processed`)
      setSuccess(`✅ Scraped ${data.scraped} matches — ${processed} new matches processed`)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Scrape failed'
      toast.error(message)
      setError(message)
    } finally { setLoading(false) }
  }

  async function handleSearchChange(idx: number, value: string) {
    updateRow(idx, { name: value, player_id: undefined });
    setSearch(value);

    if (value.length < 2) {
      setSuggestions([]);
      return;
    }

    const teamFilter = [homeCode, awayCode]
      .filter((c) => c.trim().length > 0)
      .map((c) => `iso_code=${encodeURIComponent(c.toUpperCase())}`)
      .join('&');

    const url = teamFilter
      ? `${API_BASE}/api/v1/auction/players?search=${encodeURIComponent(value)}&${teamFilter}&limit=8`
      : `${API_BASE}/api/v1/auction/players?search=${encodeURIComponent(value)}&limit=8`;

    try {
      const res = await fetch(url);
      const data = await res.json();
      setSuggestions(data.players ?? []);
    } catch {
      setSuggestions([]);
    }
  }

  function selectPlayer(idx: number, s: any) {
    updateRow(idx, { player_id: s.id, name: s.name });
    setSuggestions([]);
    setSearch("");
  }

  return (
    <div style={pageStyle}>
      <div style={card}>
        <div style={eyebrow}>Admin — Match Entry</div>
        <div style={sectionTitle}>Submit Match Result</div>
      </div>

      <div style={card}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 220px', gap: 12 }}>
          <div>
            <label style={fieldLabel}>Match ID</label>
            <input style={inputStyle} value={matchId} onChange={(e) => setMatchId(e.target.value)} />
          </div>
          <div>
            <label style={fieldLabel}>Stage</label>
            <select style={selectStyle} value={stage} onChange={(e) => setStage(e.target.value)}>
              <option value="GROUP">Group Stage</option>
              <option value="R32">Round of 32</option>
              <option value="R16">Round of 16</option>
              <option value="QF">Quarter-Final</option>
              <option value="SF">Semi-Final</option>
              <option value="THIRD_PLACE">Third Place</option>
              <option value="FINAL">Final</option>
            </select>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '120px 120px 1fr 1fr', gap: 12 }}>
          <div>
            <label style={fieldLabel}>Home Code</label>
            <input style={inputStyle} value={homeCode} onChange={(e) => setHomeCode(e.target.value.toUpperCase())} />
          </div>
          <div>
            <label style={fieldLabel}>Away Code</label>
            <input style={inputStyle} value={awayCode} onChange={(e) => setAwayCode(e.target.value.toUpperCase())} />
          </div>
          <div>
            <label style={fieldLabel}>Home Score</label>
            <input type="number" style={inputStyle} value={homeScore as any} onChange={(e) => setHomeScore(e.target.value === '' ? '' : Number(e.target.value))} />
          </div>
          <div>
            <label style={fieldLabel}>Away Score</label>
            <input type="number" style={inputStyle} value={awayScore as any} onChange={(e) => setAwayScore(e.target.value === '' ? '' : Number(e.target.value))} />
          </div>
        </div>
      </div>

      <div style={card}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={eyebrow}>Player Performances</div>
            <div style={{ color: 'rgba(255,255,255,0.7)', fontSize: 13 }}>{rows.length} player{rows.length !== 1 ? 's' : ''} added</div>
          </div>
          <button style={ghostBtn} onClick={addRow}>+ Add Player</button>
        </div>

        {rows.length === 0 ? (
          <EmptyState
            icon="📝"
            title="No player performances yet"
            description="Add player rows to record goals, assists, minutes, and cards for this match."
            action={{ label: "+ Add Player", onClick: addRow }}
          />
        ) : (
          <div style={{ display: 'grid', gap: 12, marginTop: 12 }}>
            {rows.map((p, i) => (
              <div key={i} style={{ display: 'grid', gap: 8 }}>
              <div>
                <label style={fieldLabel}>Player Name</label>
                <input style={inputStyle} value={p.name ?? ''} onChange={(e) => handleSearchChange(i, e.target.value)} />
                {search.length >= 2 && suggestions.length > 0 && (
                  <div style={{ marginTop: 6, borderRadius: 8, overflow: 'hidden', border: '1px solid rgba(255,255,255,0.04)' }}>
                    {suggestions.map((s: any) => (
                      <div
                        key={s.id}
                        onClick={() => selectPlayer(i, s)}
                        style={{
                          padding: '9px 14px',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: 10,
                          borderBottom: '1px solid rgba(255,255,255,0.05)',
                          fontSize: 13,
                          color: '#e8eaf0',
                        }}
                        onMouseEnter={e => (e.currentTarget.style.background = 'rgba(255,255,255,0.07)')}
                        onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                      >
                        <div style={{ fontWeight: 700 }}>{s.name}</div>
                        <div style={{ color: 'rgba(255,255,255,0.6)' }}>{s.position} · {s.club}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, minmax(0, 1fr))', gap: 8, alignItems: 'center' }}>
                <div>
                  <label style={fieldLabel}>Goals</label>
                  <input style={inputStyle} type="number" value={p.goals ?? ''} onChange={(e) => updateRow(i, { goals: e.target.value === '' ? undefined : Number(e.target.value) })} />
                </div>
                <div>
                  <label style={fieldLabel}>Assists</label>
                  <input style={inputStyle} type="number" value={p.assists ?? ''} onChange={(e) => updateRow(i, { assists: e.target.value === '' ? undefined : Number(e.target.value) })} />
                </div>
                <div>
                  <label style={fieldLabel}>Minutes</label>
                  <input style={inputStyle} type="number" value={p.minutes_played ?? ''} onChange={(e) => updateRow(i, { minutes_played: e.target.value === '' ? undefined : Number(e.target.value) })} />
                </div>
                <div>
                  <label style={fieldLabel}>Yellow</label>
                  <input style={inputStyle} type="number" value={p.yellow_cards ?? ''} onChange={(e) => updateRow(i, { yellow_cards: e.target.value === '' ? undefined : Number(e.target.value) })} />
                </div>
                <div>
                  <label style={fieldLabel}>Red</label>
                  <input style={inputStyle} type="number" value={p.red_cards ?? ''} onChange={(e) => updateRow(i, { red_cards: e.target.value === '' ? undefined : Number(e.target.value) })} />
                </div>
                <div>
                  <label style={fieldLabel}>Saves</label>
                  <input style={inputStyle} type="number" value={p.saves ?? ''} onChange={(e) => updateRow(i, { saves: e.target.value === '' ? undefined : Number(e.target.value) })} />
                </div>
              </div>

              <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                <label style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <input type="checkbox" checked={!!p.clean_sheet} onChange={(e) => updateRow(i, { clean_sheet: e.target.checked })} style={{ width: 18, height: 18, cursor: 'pointer', accentColor: '#d4af37' }} />
                  <span style={{ color: 'rgba(255,255,255,0.75)' }}>Clean Sheet</span>
                </label>
                <button style={dangerBtn} onClick={() => removeRow(i)}>Remove</button>
              </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div style={card}>
        {error && <div style={{ color: '#f87171' }}>{error}</div>}
        {success && <div style={{ color: '#22c55e' }}>{success}</div>}
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <button style={primaryBtn} onClick={handleSubmit} disabled={loading}>{loading ? 'Processing...' : 'Submit Result'}</button>
          <button style={ghostBtn} onClick={handleScrape} disabled={loading}>🔄 Scrape Latest WC Results</button>
          <button
            style={ghostBtn}
            onClick={() => setShowRecalcConfirm(true)}
            disabled={loading}
          >
            Recalculate All Points
          </button>
        </div>
      </div>

      <ConfirmDialog
        isOpen={showRecalcConfirm}
        title="Recalculate all points?"
        description="This will reprocess every match and update league points. This action can change standings."
        confirmLabel="Recalculate"
        cancelLabel="Keep Current"
        danger
        onConfirm={() => {
          setShowRecalcConfirm(false)
          void (async () => {
            setLoading(true)
            setError('')
            setSuccess('')
            console.log('Hitting recalculate endpoint:', `${API_BASE}/api/v1/admin/matches/recalculate`)
            try {
              const res = await fetch(`${API_BASE}/api/v1/admin/matches/recalculate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
              })
              console.log('Recalculate status:', res.status)
              const data = await res.json()
              console.log('Recalculate response:', data)
              if (!res.ok) {
                const message = data.detail ?? data.message ?? `Error ${res.status}`
                toast.error(message)
                setError(message)
                return
              }
              setSuccess(`✅ Recalculated points from ${data.count} match${data.count !== 1 ? 'es' : ''}`)
            } catch (err) {
              console.error('Recalculate error:', err)
              const message = err instanceof Error ? err.message : 'Network error — is the backend running?'
              toast.error(message)
              setError(message)
            } finally {
              setLoading(false)
            }
          })()
        }}
        onCancel={() => setShowRecalcConfirm(false)}
      />
    </div>
  );
}
