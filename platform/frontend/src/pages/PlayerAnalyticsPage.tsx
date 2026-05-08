import { motion } from "framer-motion";
import { PageHeader } from "@/components/layout";
import { PlayerCard } from "@/components/cards/PlayerCard";

const players = [
  { surname: "MBAPPÉ", firstName: "Kylian", country: "France", flag: "🇫🇷", pos: "FWD", form: 94, metrics: [{ label: "Goals", value: 28 }, { label: "Assists", value: 11 }, { label: "Minutes", value: "2,840" }, { label: "Rating", value: "8.4" }] },
  { surname: "HAALAND", firstName: "Erling", country: "Norway", flag: "🇳🇴", pos: "FWD", form: 92, metrics: [{ label: "Goals", value: 34 }, { label: "Assists", value: 7 }, { label: "Minutes", value: "2,680" }, { label: "Rating", value: "8.2" }] },
  { surname: "BELLINGHAM", firstName: "Jude", country: "England", flag: "🏴󠁧󠁢󠁥󠁮󠁧󠁿", pos: "MID", form: 91, metrics: [{ label: "Goals", value: 16 }, { label: "Assists", value: 14 }, { label: "Minutes", value: "3,020" }, { label: "Rating", value: "8.1" }] },
  { surname: "VINÍCIUS JR", firstName: "Vinícius", country: "Brazil", flag: "🇧🇷", pos: "FWD", form: 90, metrics: [{ label: "Goals", value: 22 }, { label: "Assists", value: 13 }, { label: "Minutes", value: "2,780" }, { label: "Rating", value: "8.0" }] },
  { surname: "SALAH", firstName: "Mohamed", country: "Egypt", flag: "🇪🇬", pos: "FWD", form: 89, metrics: [{ label: "Goals", value: 24 }, { label: "Assists", value: 12 }, { label: "Minutes", value: "2,920" }, { label: "Rating", value: "7.9" }] },
  { surname: "DE BRUYNE", firstName: "Kevin", country: "Belgium", flag: "🇧🇪", pos: "MID", form: 87, metrics: [{ label: "Goals", value: 10 }, { label: "Assists", value: 20 }, { label: "Minutes", value: "2,560" }, { label: "Rating", value: "7.8" }] },
  { surname: "RODRI", firstName: "Rodrigo", country: "Spain", flag: "🇪🇸", pos: "MID", form: 86, metrics: [{ label: "Goals", value: 8 }, { label: "Assists", value: 9 }, { label: "Minutes", value: "3,100" }, { label: "Rating", value: "7.7" }] },
  { surname: "SAKA", firstName: "Bukayo", country: "England", flag: "🏴󠁧󠁢󠁥󠁮󠁧󠁿", pos: "FWD", form: 88, metrics: [{ label: "Goals", value: 18 }, { label: "Assists", value: 16 }, { label: "Minutes", value: "2,900" }, { label: "Rating", value: "7.8" }] },
];

export function PlayerAnalyticsPage() {
  return (
    <div className="container-main page-section">
      <PageHeader title="Player Analytics" subtitle="Individual player intelligence dashboards with current form scoring and performance metrics" badge="Intelligence Module" />
      <div className="flex flex-wrap items-center gap-3 mb-6">
        <div className="flex items-center gap-2 overflow-x-auto">
          {["All Positions", "GK", "DEF", "MID", "FWD"].map((p, i) => (
            <button key={p} className={`px-4 py-2 rounded-full text-body-sm font-medium transition-colors whitespace-nowrap ${i === 0 ? "bg-fifa-navy text-white" : "bg-white text-text-secondary hover:bg-surface-hover border border-surface-border"}`}>{p}</button>
          ))}
        </div>
        <input type="search" placeholder="Search players…" className="ml-auto px-4 py-2 rounded-md bg-white border border-surface-border text-body-sm placeholder:text-text-tertiary w-64 focus:border-fifa-blue focus:outline-none" />
      </div>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {players.map((p, i) => (
          <motion.div key={p.surname} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }}>
            <PlayerCard surname={p.surname} firstName={p.firstName} country={p.country} countryFlag={p.flag} position={p.pos} formScore={p.form} rank={i + 1} metrics={p.metrics} />
          </motion.div>
        ))}
      </motion.div>
    </div>
  );
}
