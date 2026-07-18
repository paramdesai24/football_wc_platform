import { TEAMS } from "@/services/api";

const TEAM_ISO2: Record<string, string> = {
  Algeria: "DZ",
  Argentina: "AR",
  Australia: "AU",
  Austria: "AT",
  Belgium: "BE",
  "Bosnia and Herzegovina": "BA",
  Brazil: "BR",
  Canada: "CA",
  "Cape Verde": "CV",
  Czechia: "CZ",
  Colombia: "CO",
  Croatia: "HR",
  Curacao: "CW",
  "DR Congo": "CD",
  Ecuador: "EC",
  Egypt: "EG",
  England: "GB",
  France: "FR",
  Germany: "DE",
  Ghana: "GH",
  Haiti: "HT",
  Iran: "IR",
  Iraq: "IQ",
  "Ivory Coast": "CI",
  Italy: "IT",
  Japan: "JP",
  Jordan: "JO",
  Mexico: "MX",
  Morocco: "MA",
  Netherlands: "NL",
  "New Zealand": "NZ",
  Norway: "NO",
  Panama: "PA",
  Paraguay: "PY",
  Portugal: "PT",
  Qatar: "QA",
  "Saudi Arabia": "SA",
  Scotland: "GB",
  Senegal: "SN",
  "South Africa": "ZA",
  "South Korea": "KR",
  Spain: "ES",
  Sweden: "SE",
  Switzerland: "CH",
  Tunisia: "TN",
  Turkey: "TR",
  "United States": "US",
  Uruguay: "UY",
  Uzbekistan: "UZ",
};

const UID_TO_NAME: Record<string, string> = Object.fromEntries(
  Object.entries(TEAMS).map(([name, uid]) => [uid, name])
);

const TEAM_FLAG_CODE: Record<string, string> = {
  ...Object.fromEntries(Object.entries(TEAM_ISO2).map(([name, code]) => [name, code.toLowerCase()])),
  England: "gb-eng",
  Scotland: "gb-sct",
};

function iso2ToFlag(iso2: string): string {
  if (!iso2 || iso2.length !== 2) return "🏳";
  const code = iso2.toUpperCase();
  const first = code.codePointAt(0);
  const second = code.codePointAt(1);
  if (!first || !second) return "🏳";
  return String.fromCodePoint(127397 + first, 127397 + second);
}

export function teamFlagCode(teamOrUid: string): string {
  const name = teamNameFromUid(teamOrUid);
  const code = TEAM_FLAG_CODE[name];
  if (code) return code;

  if (teamOrUid.startsWith("C_")) {
    const raw = teamOrUid.slice(2).split("-")[0] || "";
    if (raw) return raw.toLowerCase() === "gb" ? "gb-eng" : raw.toLowerCase();
  }

  return "";
}

export function teamNameFromUid(uidOrName: string): string {
  return UID_TO_NAME[uidOrName] ?? uidOrName;
}

export function teamFlag(teamOrUid: string): string {
  const name = teamNameFromUid(teamOrUid);
  const code = TEAM_ISO2[name];
  if (code) return iso2ToFlag(code);

  if (teamOrUid.startsWith("C_")) {
    const raw = teamOrUid.slice(2).split("-")[0] || "";
    if (raw.length === 2) return iso2ToFlag(raw);
  }

  return "🏳";
}

export function withFlag(teamOrUid: string): string {
  const name = teamNameFromUid(teamOrUid);
  return `${teamFlag(teamOrUid)} ${name}`;
}

export function parseMatchLabel(match: string): { home: string; away: string } {
  const [left, right] = match.split(" vs ");
  return {
    home: left ? teamNameFromUid(left.trim()) : "Home",
    away: right ? teamNameFromUid(right.trim()) : "Away",
  };
}
