import { motion } from "framer-motion";
import { PageHeader } from "@/components/layout";

const rankings = [
  { rank: 1, name: "Argentina", code: "ARG", flag: "🇦🇷", conf: "CONMEBOL", elo: 2072, atk: 91, def: 87, form: 92, trend: "stable" },
  { rank: 2, name: "France", code: "FRA", flag: "🇫🇷", conf: "UEFA", elo: 2048, atk: 93, def: 85, form: 89, trend: "up" },
  { rank: 3, name: "Brazil", code: "BRA", flag: "🇧🇷", conf: "CONMEBOL", elo: 2012, atk: 89, def: 82, form: 85, trend: "down" },
  { rank: 4, name: "England", code: "ENG", flag: "🏴󠁧󠁢󠁥󠁮󠁧󠁿", conf: "UEFA", elo: 1998, atk: 88, def: 84, form: 87, trend: "up" },
  { rank: 5, name: "Spain", code: "ESP", flag: "🇪🇸", conf: "UEFA", elo: 1985, atk: 90, def: 83, form: 88, trend: "up" },
  { rank: 6, name: "Germany", code: "GER", flag: "🇩🇪", conf: "UEFA", elo: 1962, atk: 86, def: 84, form: 82, trend: "stable" },
  { rank: 7, name: "Portugal", code: "POR", flag: "🇵🇹", conf: "UEFA", elo: 1955, atk: 88, def: 81, form: 86, trend: "up" },
  { rank: 8, name: "Netherlands", code: "NED", flag: "🇳🇱", conf: "UEFA", elo: 1940, atk: 85, def: 83, form: 80, trend: "down" },
  { rank: 9, name: "Italy", code: "ITA", flag: "🇮🇹", conf: "UEFA", elo: 1928, atk: 82, def: 86, form: 78, trend: "stable" },
  { rank: 10, name: "Croatia", code: "CRO", flag: "🇭🇷", conf: "UEFA", elo: 1915, atk: 84, def: 82, form: 81, trend: "down" },
];

const trendIcon = (t: string) => t === "up" ? <span className="text-status-win text-xs font-bold">▲</span> : t === "down" ? <span className="text-status-loss text-xs font-bold">▼</span> : <span className="text-text-tertiary text-xs">—</span>;

export function RankingsPage() {
  return (
    <div className="container-main page-section">
      <PageHeader title="Country Rankings" subtitle="Composite team strength rankings combining Elo ratings, current form, and attack/defense metrics" badge="Intelligence Module" />
      <div className="flex items-center gap-2 mb-6 overflow-x-auto pb-2">
        {["All", "UEFA", "CONMEBOL", "CONCACAF", "CAF", "AFC", "OFC"].map((c, i) => (
          <button key={c} className={`px-4 py-2 rounded-full text-body-sm font-medium transition-colors whitespace-nowrap ${i === 0 ? "bg-fifa-navy text-white" : "bg-white text-text-secondary hover:bg-surface-hover border border-surface-border"}`}>{c}</button>
        ))}
      </div>
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="card-surface overflow-hidden">
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead><tr><th className="w-16">#</th><th>Country</th><th className="hidden md:table-cell">Conf</th><th className="text-right">Elo</th><th className="text-right hidden sm:table-cell">Atk</th><th className="text-right hidden sm:table-cell">Def</th><th className="text-right">Form</th><th className="w-12 text-center">Trend</th></tr></thead>
            <tbody>
              {rankings.map((t, i) => (
                <motion.tr key={t.code} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.04 }} className="group cursor-pointer">
                  <td><span className="stat-value text-body-md text-text-tertiary">{t.rank}</span></td>
                  <td><div className="flex items-center gap-3"><span className="text-xl">{t.flag}</span><span className="font-display font-semibold text-text-primary group-hover:text-fifa-blue transition-colors">{t.name}</span><span className="text-caption text-text-tertiary ml-2 hidden sm:inline">{t.code}</span></div></td>
                  <td className="hidden md:table-cell"><span className="badge badge-fifa text-[11px]">{t.conf}</span></td>
                  <td className="text-right"><span className="stat-value text-heading-sm text-text-primary">{t.elo}</span></td>
                  <td className="text-right hidden sm:table-cell"><span className="text-body-md text-text-primary font-medium">{t.atk}</span></td>
                  <td className="text-right hidden sm:table-cell"><span className="text-body-md text-text-primary font-medium">{t.def}</span></td>
                  <td className="text-right"><span className="stat-value text-body-md text-text-primary">{t.form}</span></td>
                  <td className="text-center">{trendIcon(t.trend)}</td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>
    </div>
  );
}
