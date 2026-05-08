import { motion } from "framer-motion";
import { PageHeader } from "@/components/layout";
import { StatCard, StatRow } from "@/components/ui/StatCard";

export function TeamAnalyticsPage() {
  return (
    <div className="container-main page-section">
      <PageHeader title="Team Analytics" subtitle="National team deep-dives with squad strength, form trends, and positional analysis" badge="Analytics Module" />
      <div className="flex items-center gap-3 mb-6">
        <select className="px-4 py-2.5 rounded-md bg-white border border-surface-border text-body-sm">
          <option>Select a team…</option><option>Argentina</option><option>France</option><option>Brazil</option><option>England</option><option>Spain</option>
        </select>
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard label="Elo Rating" value="2,072" trend="up" trendValue="+14" variant="highlight" />
        <StatCard label="Squad Strength" value="88.4" subValue="Top 3 globally" />
        <StatCard label="Avg Age" value="27.2" subValue="Optimal range" />
        <StatCard label="Market Value" value="€1.2B" trend="up" trendValue="+8%" />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="card-surface p-6">
          <h3 className="font-display text-heading-md text-text-primary mb-4">Position Strength</h3>
          <div className="space-y-1">
            <StatRow label="Goalkeeping" value={85} barColor="bg-amber-500" />
            <StatRow label="Defense" value={87} barColor="bg-blue-500" />
            <StatRow label="Midfield" value={90} barColor="bg-emerald-500" />
            <StatRow label="Attack" value={93} barColor="bg-red-500" />
          </div>
        </motion.div>
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="card-surface p-6">
          <h3 className="font-display text-heading-md text-text-primary mb-4">Recent Form</h3>
          <div className="space-y-3">
            {[{ h: "Argentina", a: "Brazil", sc: "2-1", r: "W" }, { h: "Argentina", a: "Uruguay", sc: "1-0", r: "W" }, { h: "Colombia", a: "Argentina", sc: "1-1", r: "D" }, { h: "Argentina", a: "Chile", sc: "3-0", r: "W" }, { h: "Paraguay", a: "Argentina", sc: "0-2", r: "W" }].map((m, i) => (
              <div key={i} className="flex items-center gap-3 py-2 border-b border-surface-border last:border-0">
                <span className={`w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-bold text-white ${m.r === "W" ? "bg-status-win" : m.r === "D" ? "bg-status-draw" : "bg-status-loss"}`}>{m.r}</span>
                <span className="text-body-sm text-text-primary">{m.h} {m.sc} {m.a}</span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
