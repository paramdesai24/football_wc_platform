import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { API_BASE } from "@/services/api";
import { toast } from "@/store/toastStore";
import { useIdentityStore } from "@/store/identityStore";

function fieldLabel(_labelText?: string): React.CSSProperties {
  return {
    display: "block",
    marginBottom: 4,
    fontSize: 10,
    fontWeight: 600,
    letterSpacing: "0.14em",
    textTransform: "uppercase",
    color: "rgba(212,175,55,0.75)",
    fontFamily: "var(--font-ui)",
  };
}

function inputStyle(): React.CSSProperties {
  return {
    width: "100%",
    background: "rgba(255,255,255,0.05)",
    border: "1px solid rgba(255,255,255,0.12)",
    borderRadius: 10,
    color: "#fff",
    padding: "12px 14px",
    fontFamily: "var(--font-ui)",
    fontSize: 14,
    outline: "none",
  };
}

function actionButton(primary = true): React.CSSProperties {
  return {
    width: "100%",
    minHeight: 46,
    borderRadius: 12,
    border: primary ? "1px solid rgba(212,175,55,0.55)" : "1px solid rgba(255,255,255,0.12)",
    background: primary ? "linear-gradient(180deg, #d9b74e 0%, #c79d24 100%)" : "rgba(255,255,255,0.05)",
    color: primary ? "#111827" : "#fff",
    fontFamily: "var(--font-ui)",
    fontSize: 14,
    fontWeight: 700,
    cursor: "pointer",
  };
}

export default function AuctionLobbyPage() {
  const navigate = useNavigate();
  const userId = useIdentityStore((s) => s.userId);
  const username = useIdentityStore((s) => s.username);
  const teamName = useIdentityStore((s) => s.teamName);
  const setIdentityUserId = useIdentityStore((s) => s.setUserId);
  const setIdentityUsername = useIdentityStore((s) => s.setUsername);
  const setIdentityTeamName = useIdentityStore((s) => s.setTeamName);

  const [createForm, setCreateForm] = useState({ name: "", host_id: "", budget: 50000, squad_size: 20 });
  const [joinForm, setJoinForm] = useState({ invite_code: "", user_id: "", team_name: "" });
  const [rejoinForm, setRejoinForm] = useState({ invite_code: "", user_id: "" });
  const [createLoading, setCreateLoading] = useState(false);
  const [joinLoading, setJoinLoading] = useState(false);
  const [rejoinLoading, setRejoinLoading] = useState(false);
  const [createError, setCreateError] = useState("");
  const [joinError, setJoinError] = useState("");
  const [rejoinError, setRejoinError] = useState("");
  const [inviteCode, setInviteCode] = useState("");
  const [createdLeagueId, setCreatedLeagueId] = useState("");


  async function handleCreate() {
    setCreateLoading(true);
    setCreateError("");
    try {
      const res = await fetch(`${API_BASE}/api/v1/leagues/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: createForm.name,
          host_id: createForm.host_id,
          budget: createForm.budget,
          squad_size: createForm.squad_size,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? "Failed to create league");
      toast.success(`League created! Invite code: ${data.invite_code}`);
      setInviteCode(String(data.invite_code ?? ""));
      setCreatedLeagueId(String(data.league_id ?? ""));
      // Auto-join the host so they immediately enter the auction room with host controls
      try {
        const invite = String(data.invite_code ?? "").trim().toUpperCase();
        const joinRes = await fetch(`${API_BASE}/api/v1/leagues/${invite}/join`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: createForm.host_id,
            team_name: `${createForm.host_id}'s XI`,
          }),
        });
        const joinData = await joinRes.json();
        if (!joinRes.ok) throw new Error(joinData.detail ?? 'Failed to join newly created league');
        // navigate into the auction room as the host
        navigate(`/auction/room/${joinData.league_id}?userId=${createForm.host_id}&username=${encodeURIComponent(createForm.host_id)}`);
        return;
      } catch (err) {
        // If auto-join fails, surface the error but keep the invite code visible
        setCreateError(err instanceof Error ? err.message : String(err));
      }
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : String(error);
      toast.error(message);
      setCreateError(message);
    } finally {
      setCreateLoading(false);
    }
  }

  async function handleJoin() {
    setJoinLoading(true);
    setJoinError("");
    try {
      const invite = joinForm.invite_code.trim().toUpperCase();
      const res = await fetch(`${API_BASE}/api/v1/leagues/${invite}/join`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: joinForm.user_id, team_name: joinForm.team_name }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? "Failed to join league");
      navigate(`/auction/room/${data.league_id}?userId=${joinForm.user_id}&username=${encodeURIComponent(joinForm.user_id)}&teamName=${encodeURIComponent(joinForm.team_name)}`);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : String(error);
      toast.error(message);
      setJoinError(message);
    } finally {
      setJoinLoading(false);
    }
  }

  async function handleRejoin() {
    setRejoinLoading(true);
    setRejoinError("");
    try {
      const invite = rejoinForm.invite_code.trim().toUpperCase();
      const res = await fetch(`${API_BASE}/api/v1/leagues/${invite}/rejoin`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: rejoinForm.user_id }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? "Failed to rejoin league");

      // Set global client identity
      setIdentityUserId(rejoinForm.user_id);
      setIdentityUsername(rejoinForm.user_id);
      if (data.team_name) {
        setIdentityTeamName(data.team_name);
      }

      toast.success("Welcome back! Redirecting to auction room...");
      navigate(`/auction/room/${data.league_id}?userId=${rejoinForm.user_id}&username=${encodeURIComponent(rejoinForm.user_id)}&teamName=${encodeURIComponent(data.team_name || "")}`);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : String(error);
      toast.error(message);
      setRejoinError(message);
    } finally {
      setRejoinLoading(false);
    }
  }

  const card: React.CSSProperties = {
    background: "rgba(10,18,34,0.72)",
    backdropFilter: "blur(16px)",
    WebkitBackdropFilter: "blur(16px)",
    border: "1px solid rgba(255,255,255,0.09)",
    borderRadius: 16,
    padding: 24,
    display: "grid",
    gap: 16,
    flex: "1 1 340px",
    maxWidth: 480,
    width: "100%",
  };

  return (
    <div className="page-container" style={{ display: "grid", gap: 20 }}>
      <section className="wc-card section-card" style={{ padding: 24, display: "grid", gap: 10 }}>
        <div className="eyebrow">Auction center</div>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <h1 className="page-title" style={{ fontSize: "clamp(2rem, 4vw, 3rem)", marginBottom: 0 }}>Build your league</h1>
          <button
            onClick={() => navigate('/auction/info')}
            aria-label="Player pool and how to play"
            style={{
              background: 'rgba(255,255,255,0.06)',
              border: '1px solid rgba(255,255,255,0.12)',
              borderRadius: '50%',
              width: 36,
              height: 36,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              cursor: 'pointer',
              color: 'rgba(255,255,255,0.9)',
              flexShrink: 0,
            }}
            title="Player pool & how to play"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden>
              <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.2" fill="none" />
              <rect x="11.5" y="10.5" width="1" height="5" fill="currentColor" />
              <circle cx="12" cy="7.2" r="0.7" fill="currentColor" />
            </svg>
          </button>
        </div>
        <p className="page-sub" style={{ maxWidth: 760, margin: 0 }}>
          Create a private league or join one with an invite code, then jump into the auction room.
        </p>
      </section>

      <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "center", gap: 18, alignItems: "start" }}>
        <section className="wc-card" style={card}>
          <div style={{ display: "flex", justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: "grid", gap: 4 }}>
              <div className="eyebrow">Create league</div>
              <h2 className="wc-section-title" style={{ margin: 0, fontSize: 22 }}>Start a new auction</h2>
            </div>
            {/* info button removed from this card; use header info button */}
          </div>

          <div>
            <label style={fieldLabel()}>League name</label>
            <input className="input-field" style={inputStyle()} value={createForm.name} onChange={(event) => setCreateForm((current) => ({ ...current, name: event.target.value }))} placeholder="My League" autoComplete="off" />
          </div>

          <div>
            <label style={fieldLabel()}>Your username</label>
                <input
                  className="input-field"
                  style={inputStyle()}
                  value={createForm.host_id}
                  onChange={(event) => {
                    const value = event.target.value;
                    setCreateForm((current) => ({ ...current, host_id: value }));
                    setIdentityUserId(value);
                  }}
                  placeholder="username"
                  autoComplete="off"
                />
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <div>
              <label style={fieldLabel()}>Budget per user</label>
              <input className="input-field" style={inputStyle()} type="number" value={createForm.budget} onChange={(event) => setCreateForm((current) => ({ ...current, budget: Number(event.target.value) }))} />
            </div>
            <div>
              <label style={fieldLabel()}>Squad size</label>
              <input className="input-field" style={inputStyle()} type="number" value={createForm.squad_size} onChange={(event) => setCreateForm((current) => ({ ...current, squad_size: Number(event.target.value) }))} />
            </div>
          </div>

          {createError && <div style={{ color: "#f87171", fontSize: 13 }}>{createError}</div>}

          {!inviteCode ? (
            <button style={actionButton(true)} onClick={handleCreate} disabled={createLoading}>
              {createLoading ? "Creating..." : "Create League"}
            </button>
          ) : (
            <div style={{ display: "grid", gap: 12 }}>
              <div
                style={{
                  borderRadius: 16,
                  border: "1px solid rgba(212,175,55,0.35)",
                  background: "rgba(212,175,55,0.08)",
                  padding: 18,
                  display: "grid",
                  gap: 8,
                  textAlign: "center",
                }}
              >
                <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: "0.14em", textTransform: "uppercase", color: "rgba(212,175,55,0.75)" }}>Invite code</div>
                <div
                  style={{
                    fontFamily: "var(--font-display)",
                    fontSize: "clamp(2rem, 5vw, 3rem)",
                    lineHeight: 1,
                    fontWeight: 700,
                    color: "#e3c15c",
                    letterSpacing: "0.12em",
                    userSelect: "all",
                  }}
                >
                  {inviteCode}
                </div>
                <div style={{ fontSize: 12, color: "var(--color-text-secondary)" }}>Copy this code and share it with your league members.</div>
                <button
                  style={{ ...actionButton(false), minHeight: 40 }}
                  onClick={async () => {
                    await navigator.clipboard.writeText(inviteCode);
                  }}
                >
                  Copy invite code
                </button>
              </div>
              <div style={{ display: 'grid', gap: 8 }}>
                <button
                  style={actionButton(true)}
                  onClick={() => navigate(`/auction/room/${createdLeagueId}?userId=${createForm.host_id}&username=${encodeURIComponent(createForm.host_id)}`)}
                >
                  Enter Auction Room →
                </button>
                <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.45)', textAlign: 'center' }}>
                  Your team: <strong style={{ color: 'rgba(255,255,255,0.75)' }}>{createForm.host_id ? `${createForm.host_id}'s XI` : '—'}</strong>
                </div>
              </div>
            </div>
          )}
        </section>

        <section className="wc-card" style={card}>
          <div style={{ display: "flex", justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: "grid", gap: 4 }}>
              <div className="eyebrow">Join league</div>
              <h2 className="wc-section-title" style={{ margin: 0, fontSize: 22 }}>Enter with an invite code</h2>
            </div>
            {/* info button removed from this card; use header info button */}
          </div>

          <div>
            <label style={fieldLabel("Invite code")}>Invite code</label>
            <input className="input-field" style={inputStyle()} value={joinForm.invite_code} onChange={(event) => setJoinForm((current) => ({ ...current, invite_code: event.target.value.toUpperCase() }))} placeholder="WOLF-7742" autoComplete="off" />
          </div>

          <div>
            <label style={fieldLabel("Your username")}>Your username</label>
            <input
              className="input-field"
              style={inputStyle()}
              value={joinForm.user_id}
              onChange={(event) => {
                const value = event.target.value;
                setJoinForm((current) => ({ ...current, user_id: value }));
                setIdentityUserId(value);
              }}
              placeholder="username"
              autoComplete="off"
            />
          </div>

          <div>
            <label style={fieldLabel("Team name")}>Team name</label>
            <input
              className="input-field"
              style={inputStyle()}
              value={joinForm.team_name}
              onChange={(event) => {
                const value = event.target.value;
                setJoinForm((current) => ({ ...current, team_name: value }));
                setIdentityTeamName(value);
                setIdentityUsername(value);
              }}
              placeholder="My Dream Team"
              autoComplete="off"
            />
          </div>

          {joinError && <div style={{ color: "#f87171", fontSize: 13 }}>{joinError}</div>}

          <button style={actionButton(true)} onClick={handleJoin} disabled={joinLoading}>
            {joinLoading ? "Joining..." : "Join League"}
          </button>
        </section>

        <section className="wc-card" style={card}>
          <div style={{ display: "flex", justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: "grid", gap: 4 }}>
              <div className="eyebrow">Rejoin league</div>
              <h2 className="wc-section-title" style={{ margin: 0, fontSize: 22 }}>Return to your room</h2>
            </div>
          </div>

          <div>
            <label style={fieldLabel("Invite code")}>Invite code</label>
            <input
              className="input-field"
              style={inputStyle()}
              value={rejoinForm.invite_code}
              onChange={(event) => setRejoinForm((current) => ({ ...current, invite_code: event.target.value.toUpperCase() }))}
              placeholder="WOLF-7742"
              autoComplete="off"
            />
          </div>

          <div>
            <label style={fieldLabel("Your username")}>Your username</label>
            <input
              className="input-field"
              style={inputStyle()}
              value={rejoinForm.user_id}
              onChange={(event) => setRejoinForm((current) => ({ ...current, user_id: event.target.value }))}
              placeholder="username"
              autoComplete="off"
            />
          </div>

          {rejoinError && <div style={{ color: "#f87171", fontSize: 13 }}>{rejoinError}</div>}

          <button style={actionButton(true)} onClick={handleRejoin} disabled={rejoinLoading}>
            {rejoinLoading ? "Rejoining..." : "Rejoin League"}
          </button>
        </section>
      </div>
    </div>
  );
}
