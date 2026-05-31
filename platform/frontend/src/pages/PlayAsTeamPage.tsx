/**
 * Play As A Team — three-phase progressive simulation UX.
 */

import { useEffect, useState } from "react";
import type { PlayAsTeamResponse, TournamentStateResponse, TournamentMatchResponse } from "@/contracts";
import { apiGet, apiPost, stageTitle, TEAM_NAMES } from "@/services/api";
import { FlagImg } from "@/components/FlagImg";
import { teamFlagCode } from "@/lib/flags";

type MatchEvent = {
  minute: string;
  type: string;
  team: string;
  description?: string;
};

type SimMatch = {
  stage: string;
  homeTeam: string;
  homeCode: string;
  awayTeam: string;
  awayCode: string;
  score: string;
  events: MatchEvent[];
};

type SimSummary = {
  index: number;
  finalPosition: string;
  positionEmoji: string;
  matches: SimMatch[];
};

type Phase = "grid" | "detail" | "match";

function getPositionEmoji(position: string): string {
  const p = (position || "").toLowerCase();
  if (p.includes("champion") || p.includes("winner")) return "🏆";
  // Check more specific stages first to avoid substring collisions (e.g. "quarter-final" contains "final")
  if (p.includes("quarter")) return "QF";
  if (p.includes("semi")) return "SF";
  if (p.includes("round of 16")) return "R16";
  if (p.includes("round of 32")) return "R32";
  if (p.includes("runner") || p.includes("final") || p.includes("second")) return "🥈";
  if (p.includes("third")) return "🥉";
  if (p.includes("fourth") || p.includes("4th")) return "4️⃣";
  return (position || "?").slice(0, 3).toUpperCase();
}

function mapJourneyToSimSummary(journey: Record<string, unknown>, index: number, teamName: string): SimSummary {
  const finalPosition = String(journey.stage_reached ?? journey.final_position ?? journey.result ?? "Unknown");
  const rawMatches = Array.isArray(journey.matches)
    ? journey.matches
    : Array.isArray(journey.path)
      ? journey.path
      : Array.isArray(journey.games)
        ? journey.games
        : Array.isArray(journey.events)
          ? journey.events
          : [];

  const matches: SimMatch[] = rawMatches.map((rawMatch) => {
    const match = rawMatch as Record<string, unknown>;
    const opponent = String(match.opponent ?? match.away_team ?? match.home_team ?? "TBD");
    const teamIsHome = typeof match.is_home === "boolean" ? Boolean(match.is_home) : !match.away_team;
    const homeTeam = String(match.home_team ?? (teamIsHome ? teamName : opponent));
    const awayTeam = String(match.away_team ?? (teamIsHome ? opponent : teamName));
    const score =
      match.home_score != null && match.away_score != null
        ? `${match.home_score}-${match.away_score}`
        : match.goals_for != null && match.goals_against != null
          ? teamIsHome
            ? `${match.goals_for}-${match.goals_against}`
            : `${match.goals_against}-${match.goals_for}`
          : "TBD";

    const events: MatchEvent[] = (Array.isArray(match.timeline) ? match.timeline : []).map((rawEvent) => {
      const event = rawEvent as Record<string, unknown>;
      return {
        minute: String(event.minute ?? ""),
        type: String(event.label ?? event.event_type ?? event.type ?? "Event"),
        team: String(event.team ?? ""),
        description: String(event.note ?? event.description ?? "") || undefined,
      };
    });

    return {
      stage: String(match.stage_label ?? match.stage ?? stageTitle(String(match.stage ?? ""))),
      homeTeam,
      homeCode: teamFlagCode(homeTeam),
      awayTeam,
      awayCode: teamFlagCode(awayTeam),
      score,
      events,
    };
  });

  return {
    index: index + 1,
    finalPosition,
    positionEmoji: getPositionEmoji(finalPosition),
    matches,
  };
}

export default function PlayAsTeamPage() {
  const [availableTeams, setAvailableTeams] = useState<string[]>(TEAM_NAMES);
  const [selectedTeam, setSelectedTeam] = useState("Argentina");
  const [simulations, setSimulations] = useState(10);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PlayAsTeamResponse | null>(null);
  const [error, setError] = useState("");

  const [phase, setPhase] = useState<Phase>("grid");
  const [simResults, setSimResults] = useState<SimSummary[]>([]);
  const [selectedSim, setSelectedSim] = useState<SimSummary | null>(null);
  const [selectedMatchIdx, setSelectedMatchIdx] = useState(0);
  const [loadedCount, setLoadedCount] = useState(0);

  useEffect(() => {
    apiGet<TournamentStateResponse>("/api/v1/tournament_results?refresh=false")
      .then((res) => {
        if (res.error) {
          console.error("Tournament state fetch failed:", res.error);
          return;
        }
        if (res.data) {
          console.log("Tournament state response:", res.data);
          const state = res.data as TournamentStateResponse;
          const matches = (state.matches ?? []) as TournamentMatchResponse[];
          const teams = new Set<string>();
          matches.forEach((m) => {
            const home = String(m.home_team ?? "").trim();
            const away = String(m.away_team ?? "").trim();
            if (home) teams.add(home);
            if (away) teams.add(away);
          });
          if (teams.size > 0) {
            const sorted = [...teams].sort();
            setAvailableTeams(sorted);
            if (!sorted.includes(selectedTeam) && sorted.length > 0) {
              setSelectedTeam(sorted.includes("Argentina") ? "Argentina" : (sorted[0] || ""));
            }
          }
        }
      })
      .catch((err) => {
        console.error("Tournament state fetch failed:", err);
        setError(String(err));
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const simulation = result as unknown as { matches?: unknown; paths?: unknown; journeys?: unknown } | null;
    console.log(
      "Simulation matches raw:",
      JSON.stringify(simulation?.matches ?? simulation?.paths ?? simulation?.journeys ?? simulation, null, 2),
    );
  }, [result]);

  useEffect(() => {
    const rawSimResults = Array.isArray(result?.journeys) ? result?.journeys : [];
    const resultTeam = String((result as { team?: string } | null)?.team ?? selectedTeam);

    if (rawSimResults.length === 0) {
      setSimResults([]);
      setSelectedSim(null);
      setSelectedMatchIdx(0);
      setLoadedCount(0);
      setPhase("grid");
      return;
    }

    setPhase("grid");
    setSelectedSim(null);
    setSelectedMatchIdx(0);
    setSimResults([]);
    setLoadedCount(0);

    const timers: number[] = [];
    const summaries = rawSimResults.map((journey, index) => mapJourneyToSimSummary(journey as Record<string, unknown>, index, resultTeam));

    summaries.forEach((summary, index) => {
      const timer = window.setTimeout(() => {
        setSimResults((prev) => {
          const next = [...prev];
          next[index] = summary;
          return next.filter(Boolean) as SimSummary[];
        });
        setLoadedCount(index + 1);
      }, index * 120);
      timers.push(timer);
    });

    return () => {
      timers.forEach((timer) => window.clearTimeout(timer));
    };
  }, [result]);

  const handleSimulate = async () => {
    setLoading(true);
    setResult(null);
    setError("");
    try {
      const res = await apiPost<PlayAsTeamResponse>(
        "/api/v1/play_as",
        { team_name: selectedTeam, simulations },
        240000,
      );
      if (res.error) {
        console.error("Play As simulation failed:", res.error);
        setError(`Play As simulation failed: ${res.error}`);
      } else if (res.data) {
        const payload = (res.data as { data?: PlayAsTeamResponse }).data ?? (res.data as PlayAsTeamResponse);
        console.log("Play As response:", payload);
        setResult(payload);
      }
    } catch (err) {
      console.error("Play As simulation failed:", err);
      setError(String(err));
    } finally {
      setLoading(false);
    }
  };

  const totalSimulations =
    (result as { simulations?: number } | null)?.simulations ??
    (simResults.length || (Array.isArray(result?.journeys) ? result.journeys.length : 0));

  useEffect(() => {
    if (selectedSim?.matches?.length) {
      console.log("selectedSim.matches[0]:", selectedSim.matches[0]);
    }
  }, [selectedSim]);

  return (
    <div className="page-container">
      <section className="wc-card section-card" style={{ marginBottom: 16 }}>
        <div className="wc-card-header">
          <div className="wc-card-title-group">
            <div className="eyebrow">Simulation journeys</div>
            <h1 className="page-title" style={{ fontSize: "1.7rem" }}>Play as a team</h1>
            <p className="page-sub" style={{ maxWidth: 760, margin: 0 }}>
              Simulate multiple tournaments for one team and inspect the paths they take through the competition.
            </p>
          </div>
          <div className="wc-badge wc-badge-gold">{loading ? "SIMULATING" : "READY"}</div>
        </div>
      </section>

      <div className="wc-card" style={{ display: "grid", gap: 14, marginBottom: 16, padding: "20px 24px" }}>
        <div style={{ display: "flex", gap: 12, alignItems: "end", flexWrap: "wrap" }}>
          <div>
            <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "var(--color-text-secondary)", marginBottom: 4 }}>
              Select Team
            </label>
            <select className="select" value={selectedTeam} onChange={(e) => setSelectedTeam(e.target.value)}>
              {availableTeams.map((team) => (
                <option key={team} value={team}>
                  {team}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "var(--color-text-secondary)", marginBottom: 4 }}>
              Simulations
            </label>
            <input
              type="number"
              className="input-field"
              min={1}
              max={25}
              value={simulations}
              onChange={(e) => setSimulations(Number(e.target.value))}
              style={{ width: 80 }}
            />
          </div>

          <button className="btn btn-primary" disabled={loading} onClick={handleSimulate}>
            {loading ? <><span className="spinner" /> Simulating...</> : "Run Play As Simulations"}
          </button>

          <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 10 }}>
            <FlagImg code={teamFlagCode(selectedTeam)} size={28} />
            <div>
              <div className="wc-stat-label">Current team</div>
              <div style={{ fontWeight: 700 }}>{selectedTeam}</div>
            </div>
          </div>
        </div>
      </div>

      {error && (
        <div
          style={{
            background: "rgba(248,81,73,0.08)",
            border: "1px solid rgba(248,81,73,0.2)",
            borderRadius: 6,
            padding: "8px 12px",
            fontSize: "0.8125rem",
            color: "var(--color-red)",
            marginBottom: 12,
          }}
        >
          {error}
        </div>
      )}

      {!result && !loading && !error && (
        <div
          style={{
            background: "rgba(88,166,255,0.08)",
            border: "1px solid rgba(88,166,255,0.2)",
            borderRadius: 6,
            padding: "8px 12px",
            fontSize: "0.8125rem",
            color: "var(--color-accent)",
          }}
        >
          ℹ Choose a team and run simulations to see tournament journeys.
        </div>
      )}

      {result && phase === "grid" && (
        <section className="wc-card" style={{ marginBottom: 16 }}>
          <div className="wc-card-header" style={{ marginBottom: 8 }}>
            <div className="wc-card-title-group">
              <div className="wc-eyebrow">Results grid</div>
              <h2 className="wc-section-title">Simulation summaries</h2>
            </div>
            <div className="wc-badge wc-badge-gold">{loadedCount} / {totalSimulations}</div>
          </div>

          {loadedCount < totalSimulations && (
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14, color: "var(--color-text-secondary)", fontSize: "0.8125rem" }}>
              <span className="spinner" />
              <span>Populating summary cards progressively...</span>
            </div>
          )}

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: '12px',
              width: '100%',
            }}
          >
            {simResults.map((sim, idx) => (
              <div
                key={sim.index}
                onClick={() => { setSelectedSim(sim); setSelectedMatchIdx(0); setPhase('detail'); }}
                style={{
                  ...(idx === simResults.length - 1 && simResults.length % 2 !== 0
                    ? { gridColumn: '1 / -1', maxWidth: 'calc(50% - 6px)', margin: '0 auto', width: '100%' }
                    : {}),
                  background: 'rgba(10, 18, 34, 0.72)',
                  backdropFilter: 'blur(16px)',
                  WebkitBackdropFilter: 'blur(16px)',
                  border: '1px solid rgba(255,255,255,0.09)',
                  borderRadius: '14px',
                  padding: '32px 20px',
                  cursor: 'pointer',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '12px',
                  minHeight: '160px',
                  transition: 'border-color 0.15s ease, transform 0.15s ease',
                }}
                onMouseEnter={e => {
                  const el = e.currentTarget as HTMLDivElement;
                  el.style.borderColor = 'rgba(212,175,55,0.45)';
                  el.style.transform = 'translateY(-3px)';
                }}
                onMouseLeave={e => {
                  const el = e.currentTarget as HTMLDivElement;
                  el.style.borderColor = 'rgba(255,255,255,0.09)';
                  el.style.transform = 'translateY(0)';
                }}
              >
                <span style={{ fontSize: '36px', lineHeight: 1 }}>{sim.positionEmoji}</span>
                <span style={{
                  fontFamily: 'var(--font-display)',
                  fontSize: '11px',
                  fontWeight: 700,
                  color: 'rgba(255,255,255,0.4)',
                  letterSpacing: '0.1em',
                  textTransform: 'uppercase',
                }}>
                  Sim {sim.index}
                </span>
                <span style={{
                  fontFamily: 'var(--font-ui)',
                  fontSize: '15px',
                  fontWeight: 700,
                  color: '#ffffff',
                  textAlign: 'center',
                }}>
                  {sim.finalPosition}
                </span>
              </div>
            ))}
          </div>
        </section>
      )}

      {phase === 'detail' && selectedSim && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>


          {/* Back button */}
          <button onClick={() => setPhase('grid')}
            style={{
              background: 'none',
              border: 'none',
              color: 'rgba(255,255,255,0.45)',
              fontFamily: 'var(--font-ui)',
              fontSize: '13px',
              fontWeight: 500,
              cursor: 'pointer',
              padding: '0 0 20px 0',
              textAlign: 'left',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            ← All simulations
          </button>

          {/* Sim header */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '2px' }}>
            <div style={{ fontSize: '36px', lineHeight: 1 }}>{selectedSim.positionEmoji}</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: '11px', fontWeight: 700, color: 'rgba(255,255,255,0.4)', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
                Simulation {selectedSim.index}
              </div>
              <div style={{ fontFamily: 'var(--font-ui)', fontSize: '14px', fontWeight: 700, color: '#ffffff' }}>
                {selectedSim.finalPosition}
              </div>
            </div>
          </div>


          {/* Match rows */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {selectedSim.matches.map((match, idx) => (
              <div key={idx}
                onClick={() => { setSelectedMatchIdx(idx); setPhase('match'); }}
                style={{
                  background: 'rgba(10, 18, 34, 0.72)',
                  backdropFilter: 'blur(16px)',
                  WebkitBackdropFilter: 'blur(16px)',
                  border: '1px solid rgba(255,255,255,0.09)',
                  borderRadius: '10px',
                  padding: '14px 18px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '12px',
                  transition: 'border-color 0.15s ease, transform 0.12s ease',
                }}
                onMouseEnter={e => {
                  (e.currentTarget as HTMLDivElement).style.borderColor = 'rgba(255,255,255,0.22)';
                  (e.currentTarget as HTMLDivElement).style.transform = 'translateY(-1px)';
                }}
                onMouseLeave={e => {
                  (e.currentTarget as HTMLDivElement).style.borderColor = 'rgba(255,255,255,0.09)';
                  (e.currentTarget as HTMLDivElement).style.transform = 'translateY(0)';
                }}
              >
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', minWidth: 0, flex: 1 }}>
                  <div style={{ fontSize: '10px', fontWeight: 600, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'rgba(212, 175, 55, 0.7)', fontFamily: 'var(--font-ui)', lineHeight: 1 }}>
                    {match.stage}
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px', minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', minWidth: 0, flex: 1 }}>
                      <FlagImg code={match.homeCode} size={18} />
                      <span style={{ fontSize: '0.95rem', fontWeight: 700, color: '#ffffff', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{match.homeTeam}</span>
                    </div>

                    <div style={{ fontFamily: 'var(--font-display)', fontSize: '1.45rem', fontWeight: 800, color: '#ffffff', letterSpacing: '0.04em', flexShrink: 0 }}>
                      {match.score}
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', minWidth: 0, flex: 1, justifyContent: 'flex-end' }}>
                      <span style={{ fontSize: '0.95rem', fontWeight: 700, color: '#ffffff', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', textAlign: 'right' }}>{match.awayTeam}</span>
                      <FlagImg code={match.awayCode} size={18} />
                    </div>
                  </div>
                </div>

                <div style={{ color: 'rgba(255,255,255,0.45)', fontSize: '1.25rem', lineHeight: 1, flexShrink: 0 }}>›</div>
              </div>
            ))}
          </div>

        </div>
      )}

      {phase === 'match' && selectedSim && (() => {
        const match = selectedSim.matches[selectedMatchIdx] ?? selectedSim.matches[0];
        if (!match) return null;
        const isFirst = selectedMatchIdx === 0;
        const isLast = selectedMatchIdx === selectedSim.matches.length - 1;

        function evColor(type: string): string {
          const t = (type || '').toLowerCase();
          if (t.includes('goal') || t.includes('winner') || t.includes('equalizer')) return '#22c55e';
          if (t.includes('yellow')) return '#f59e0b';
          if (t.includes('red card')) return '#ef4444';
          return 'rgba(255,255,255,0.82)';
        }

        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>


            {/* Back to match list */}
            <button onClick={() => setPhase('detail')}
              style={{
                background: 'none',
                border: 'none',
                color: 'rgba(255,255,255,0.45)',
                fontFamily: 'var(--font-ui)',
                fontSize: '13px',
                fontWeight: 500,
                cursor: 'pointer',
                padding: '0 0 20px 0',
                textAlign: 'left',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              ← Match list
            </button>

            {/* Full match card */}
            <div style={{
              background: 'rgba(10, 18, 34, 0.72)',
              backdropFilter: 'blur(16px)',
              WebkitBackdropFilter: 'blur(16px)',
              border: '1px solid rgba(255,255,255,0.09)',
              borderRadius: '14px',
              padding: '18px 20px',
              display: 'flex',
              flexDirection: 'column',
              gap: '14px',
            }}>

              {/* Card header — stage + teams + score */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>

                {/* Stage + match counter */}
                <div style={{ fontSize: '10px', fontWeight: 600, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'rgba(212, 175, 55, 0.7)', fontFamily: 'var(--font-ui)', lineHeight: 1 }}>
                  {match.stage} · Match {selectedMatchIdx + 1} of {selectedSim.matches.length}
                </div>

                {/* Teams + score */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px' }}>

                  {/* Home */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', minWidth: 0, flex: 1 }}>
                    <FlagImg code={match.homeCode} size={28} />
                    <span style={{ fontSize: '15px', fontWeight: 600, color: '#ffffff', fontFamily: 'var(--font-ui)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {match.homeTeam}
                    </span>
                  </div>

                  {/* Score */}
                  <div style={{ fontFamily: 'var(--font-display)', fontSize: '28px', fontWeight: 800, color: '#ffffff', letterSpacing: '0.04em', padding: '0 12px', flexShrink: 0 }}>
                    {match.score}
                  </div>

                  {/* Away — flag on right */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', minWidth: 0, flex: 1, justifyContent: 'flex-end' }}>
                    <span style={{ fontSize: '15px', fontWeight: 600, color: '#ffffff', fontFamily: 'var(--font-ui)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', textAlign: 'right' }}>
                      {match.awayTeam}
                    </span>
                    <FlagImg code={match.awayCode} size={28} />
                  </div>

                </div>
              </div>

              {/* Events timeline */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0' }}>
                {(match.events || []).map((ev: any, i: number) => (
                  <div key={i} style={{ display: 'grid', gridTemplateColumns: '36px 1fr', gap: '8px', padding: '6px 0', borderBottom: '1px solid rgba(255,255,255,0.04)', alignItems: 'baseline' }}>
                    <div style={{ fontFamily: 'var(--font-display)', fontSize: '13px', fontWeight: 700, color: 'rgba(255,255,255,0.4)', textAlign: 'right', whiteSpace: 'nowrap' }}>
                      {ev.minute}
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1px' }}>
                      <div style={{ fontSize: '13px', fontWeight: 600, color: evColor(ev.type), fontFamily: 'var(--font-ui)', lineHeight: 1.3 }}>
                        {ev.type} — {ev.team}
                      </div>
                      {ev.description && (
                        <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.38)', fontFamily: 'var(--font-ui)', lineHeight: 1.4 }}>
                          {ev.description}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {/* Prev / Next navigation — INSIDE the card, at the bottom */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '4px' }}>

                {/* Previous button */}
                <button onClick={() => setSelectedMatchIdx(i => i - 1)}
                  style={{
                    flex: 1,
                    padding: '10px 0',
                    background: isFirst ? 'transparent' : 'rgba(255,255,255,0.06)',
                    border: `1px solid ${isFirst ? 'rgba(255,255,255,0.06)' : 'rgba(255,255,255,0.14)'}`,
                    borderRadius: '8px',
                    color: isFirst ? 'rgba(255,255,255,0.2)' : '#ffffff',
                    fontFamily: 'var(--font-ui)',
                    fontSize: '13px',
                    fontWeight: 600,
                    cursor: isFirst ? 'not-allowed' : 'pointer',
                  }}
                >
                  ← Previous
                </button>

                {/* Counter */}
                <div style={{ minWidth: '84px', textAlign: 'center', fontFamily: 'var(--font-display)', fontSize: '16px', fontWeight: 800, color: '#ffffff' }}>
                  {selectedMatchIdx + 1} / {selectedSim.matches.length}
                </div>

                {/* Next button */}
                <button onClick={() => setSelectedMatchIdx(i => i + 1)}
                  style={{
                    flex: 1,
                    padding: '10px 0',
                    background: isLast ? 'transparent' : '#d4af37',
                    border: `1px solid ${isLast ? 'rgba(255,255,255,0.06)' : '#d4af37'}`,
                    borderRadius: '8px',
                    color: isLast ? 'rgba(255,255,255,0.2)' : '#0a0f1a',
                    fontFamily: 'var(--font-ui)',
                    fontSize: '13px',
                    fontWeight: 600,
                    cursor: isLast ? 'not-allowed' : 'pointer',
                  }}
                >
                  Next →
                </button>

              </div>

            </div>

          </div>
        );
      })()}
    </div>
  );
}
