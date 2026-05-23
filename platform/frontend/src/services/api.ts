/**
 * API client matching the Streamlit backend integration.
 * Mirrors the http_get / http_post helpers from app.py.
 */

const API_BASE = import.meta.env.VITE_API_URL || "";

// In dev, Vite proxy forwards /api -> backend.
// The Streamlit app uses /api/v1/ prefix.

export interface ApiResult<T = unknown> {
  data?: T;
  error?: string;
}

export async function apiGet<T = unknown>(path: string, timeout = 30000): Promise<ApiResult<T>> {
  const url = `${API_BASE}${path}`;
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeout);
    const res = await fetch(url, { signal: controller.signal });
    clearTimeout(timer);
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    const json = await res.json();
    return { data: json as T };
  } catch (e: unknown) {
    return { error: e instanceof Error ? e.message : String(e) };
  }
}

export async function apiPost<T = unknown>(
  path: string,
  body: Record<string, unknown>,
  timeout = 120000
): Promise<ApiResult<T>> {
  const url = `${API_BASE}${path}`;
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeout);
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    clearTimeout(timer);
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    const json = await res.json();
    return { data: json as T };
  } catch (e: unknown) {
    return { error: e instanceof Error ? e.message : String(e) };
  }
}

/** Normalize the backend response shape (data wrapper or direct) */
export function normalizeState(response: Record<string, unknown>): Record<string, unknown> {
  const data = response?.data;
  if (data && typeof data === "object" && !Array.isArray(data)) {
    return data as Record<string, unknown>;
  }
  return response ?? {};
}

/** Teams matching the Streamlit TEAMS dict */
export const TEAMS: Record<string, string> = {
  Spain: "C_ES",
  France: "C_FR",
  Argentina: "C_AR",
  Germany: "C_DE",
  Brazil: "C_BR",
  England: "C_GB-ENG",
  Portugal: "C_PT",
  Netherlands: "C_NL",
  Italy: "C_IT",
  Belgium: "C_BE",
  Uruguay: "C_UY",
  Colombia: "C_CO",
};

export const TEAM_NAMES = Object.keys(TEAMS);

export const STAGE_ORDER = ["GROUP", "R32", "R16", "QF", "SF", "THIRD_PLACE", "FINAL"];

export function stageTitle(stage: string): string {
  const map: Record<string, string> = {
    GROUP: "Group Stage",
    R32: "Round of 32",
    R16: "Round of 16",
    QF: "Quarter-Finals",
    SF: "Semi-Finals",
    THIRD_PLACE: "Third-Place Match",
    FINAL: "Final",
  };
  return map[stage] || stage;
}

export function stageRank(stage: string): number {
  const idx = STAGE_ORDER.indexOf(stage);
  return idx >= 0 ? idx : STAGE_ORDER.length;
}

export function scoreText(match: Record<string, unknown>): string {
  const hs = match.home_score;
  const as = match.away_score;
  if (hs == null || as == null) return "TBD";
  let base = `${hs}-${as}`;
  if (match.penalties && match.penalty_score) base += ` (${match.penalty_score} pens)`;
  else if (match.extra_time) base += " AET";
  return base;
}
