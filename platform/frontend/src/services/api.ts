/**
 * API client matching the Streamlit backend integration.
 * Mirrors the http_get / http_post helpers from app.py.
 */

export const API_BASE = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || "";
export const WS_BASE = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000';

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

/** Qualified FIFA World Cup 2026 teams */
export const TEAMS: Record<string, string> = {
  Algeria: "C_DZ",
  Argentina: "C_AR",
  Australia: "C_AU",
  Austria: "C_AT",
  Belgium: "C_BE",
  "Bosnia and Herzegovina": "C_BA",
  Brazil: "C_BR",
  Canada: "C_CA",
  "Cape Verde": "C_CV",
  Czechia: "C_CZ",
  Colombia: "C_CO",
  Croatia: "C_HR",
  Curacao: "C_CW",
  "DR Congo": "C_CD",
  Ecuador: "C_EC",
  Egypt: "C_EG",
  England: "C_GB-ENG",
  France: "C_FR",
  Germany: "C_DE",
  Ghana: "C_GH",
  Haiti: "C_HT",
  Iran: "C_IR",
  Iraq: "C_IQ",
  "Ivory Coast": "C_CI",
  Japan: "C_JP",
  Jordan: "C_JO",
  Mexico: "C_MX",
  Morocco: "C_MA",
  Netherlands: "C_NL",
  "New Zealand": "C_NZ",
  Norway: "C_NO",
  Panama: "C_PA",
  Paraguay: "C_PY",
  Portugal: "C_PT",
  Qatar: "C_QA",
  "Saudi Arabia": "C_SA",
  Scotland: "C_GB-SCT",
  Senegal: "C_SN",
  "South Africa": "C_ZA",
  "South Korea": "C_KR",
  Spain: "C_ES",
  Sweden: "C_SE",
  Switzerland: "C_CH",
  Tunisia: "C_TN",
  Turkey: "C_TR",
  "United States": "C_US",
  Uruguay: "C_UY",
  Uzbekistan: "C_UZ",
  Italy: "C_IT",
};

export const TEAM_NAMES = Object.keys(TEAMS);

/** Confederation lookup for known teams (fallback when backend omits confederation) */
export const CONFED_MAP: Record<string, string> = {
  Algeria: "CAF",
  Argentina: "CONMEBOL",
  Australia: "AFC",
  Austria: "UEFA",
  Belgium: "UEFA",
  "Bosnia and Herzegovina": "UEFA",
  Brazil: "CONMEBOL",
  Canada: "CONCACAF",
  "Cape Verde": "CAF",
  Czechia: "UEFA",
  Colombia: "CONMEBOL",
  Croatia: "UEFA",
  Curacao: "CONCACAF",
  "DR Congo": "CAF",
  Ecuador: "CONMEBOL",
  Egypt: "CAF",
  England: "UEFA",
  France: "UEFA",
  Germany: "UEFA",
  Ghana: "CAF",
  Haiti: "CONCACAF",
  Iran: "AFC",
  Iraq: "AFC",
  "Ivory Coast": "CAF",
  Japan: "AFC",
  Jordan: "AFC",
  Mexico: "CONCACAF",
  Morocco: "CAF",
  Netherlands: "UEFA",
  "New Zealand": "OFC",
  Norway: "UEFA",
  Panama: "CONCACAF",
  Paraguay: "CONMEBOL",
  Portugal: "UEFA",
  Qatar: "AFC",
  "Saudi Arabia": "AFC",
  Scotland: "UEFA",
  Senegal: "CAF",
  "South Africa": "CAF",
  "South Korea": "AFC",
  Spain: "UEFA",
  Sweden: "UEFA",
  Switzerland: "UEFA",
  Tunisia: "CAF",
  Turkey: "UEFA",
  "United States": "CONCACAF",
  Uruguay: "CONMEBOL",
  Uzbekistan: "AFC",
  Italy: "UEFA",
};

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
