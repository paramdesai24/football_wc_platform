import type { CountryRankingRow } from "@/contracts";
import { CONFED_MAP } from "@/services/api";
import { FlagImg } from "@/components/FlagImg";
import { teamFlagCode } from "@/lib/flags";

const CONFEDERATION: Record<string, string> = {
  // UEFA
  ES: "UEFA", FR: "UEFA", DE: "UEFA", PT: "UEFA", NL: "UEFA", BE: "UEFA",
  IT: "UEFA", HR: "UEFA", CH: "UEFA", RS: "UEFA", PL: "UEFA", TR: "UEFA",
  GB: "UEFA", "GB-ENG": "UEFA", AT: "UEFA", CZ: "UEFA", HU: "UEFA",
  SK: "UEFA", SI: "UEFA", AL: "UEFA", GE: "UEFA", RO: "UEFA", UA: "UEFA",
  // CONMEBOL
  AR: "CONMEBOL", BR: "CONMEBOL", UY: "CONMEBOL", CO: "CONMEBOL",
  EC: "CONMEBOL", CL: "CONMEBOL", PY: "CONMEBOL", VE: "CONMEBOL",
  PE: "CONMEBOL", BO: "CONMEBOL",
  // CONCACAF
  US: "CONCACAF", MX: "CONCACAF", CA: "CONCACAF", CR: "CONCACAF",
  PA: "CONCACAF", JM: "CONCACAF", HN: "CONCACAF", SV: "CONCACAF",
  // CAF
  MA: "CAF", SN: "CAF", NG: "CAF", CM: "CAF", EG: "CAF", GH: "CAF",
  CI: "CAF", TN: "CAF", DZ: "CAF", ML: "CAF", ZA: "CAF", CD: "CAF",
  // AFC
  JP: "AFC", KR: "AFC", AU: "AFC", IR: "AFC", SA: "AFC", QA: "AFC",
  AE: "AFC", UZ: "AFC", CN: "AFC", IN: "AFC", IQ: "AFC", JO: "AFC",
  // OFC
  NZ: "OFC",
  // Special
  CV: "CAF", BA: "UEFA",
};

function normalizeCountryCode(code: string): string {
  const value = (code || "").trim().toUpperCase();
  if (!value) return "";
  if (value.startsWith("C_")) return value.slice(2);
  return value;
}

interface StandingsTableProps {
  rows: CountryRankingRow[];
  title: string;
  subtitle?: string;
  onOpenRankings?: () => void;
}

function rowTone(row: CountryRankingRow, totalRows: number): string {
  if (row.rank <= 8) return "wc-table-row-qual";
  if (row.rank > Math.max(0, totalRows - 4)) return "wc-table-row-elim";
  return "";
}

export function StandingsTable({ rows, title, subtitle, onOpenRankings }: StandingsTableProps) {
  const totalRows = rows.length;

  return (
    <section className="wc-card">
      <div className="wc-card-header">
        <div className="wc-card-title-group">
          <div className="wc-eyebrow">Standings</div>
          <h2 className="wc-section-title">{title}</h2>
          {subtitle && <p style={{ margin: 0, color: "var(--color-text-secondary)", fontSize: "0.9rem", lineHeight: 1.6 }}>{subtitle}</p>}
        </div>
        {onOpenRankings && (
          <button className="btn" onClick={onOpenRankings}>
            Full Rankings
          </button>
        )}
      </div>

      <div className="wc-table-shell">
        <table className="data-table wc-table rankings-table">
          <thead>
            <tr>
              <th className="col-rank">#</th>
              <th className="col-country">Country</th>
              <th className="col-confed">Confed.</th>
              <th className="col-num numeric">Smart Score</th>
              <th className="col-num numeric">Attack</th>
              <th className="col-num numeric">Defense</th>
              <th className="col-num numeric">Form</th>
            </tr>
          </thead>
          <tbody>
            {rows.length > 0 ? (
              rows.map((row) => (
                <tr key={row.country_uid} className={rowTone(row, totalRows)}>
                  <td className="col-rank">{row.rank}</td>
                  <td className="col-country">
                    <span className="country-cell">
                      <FlagImg code={teamFlagCode(row.country_uid) || teamFlagCode(row.country_name)} size={20} />
                      <span>{row.country_name}</span>
                    </span>
                  </td>
                  <td className="col-confed">{row.confederation || CONFEDERATION[normalizeCountryCode(teamFlagCode(row.country_uid) || row.country_uid)] || CONFEDERATION[normalizeCountryCode(teamFlagCode(row.country_name) || row.country_name)] || CONFED_MAP[row.country_name] || "—"}</td>
                  <td className="col-num numeric">{Number(row.elo_rating).toFixed(0)}</td>
                  <td className="col-num numeric">{Number(row.attack_rating).toFixed(1)}</td>
                  <td className="col-num numeric">{Number(row.defense_rating).toFixed(1)}</td>
                  <td className="col-num numeric">{row.recent_form_score != null ? `${(Number(row.recent_form_score) * 100).toFixed(1)}%` : "-"}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={7} style={{ color: "var(--color-text-muted)", padding: 16 }}>
                  No standings data available yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
