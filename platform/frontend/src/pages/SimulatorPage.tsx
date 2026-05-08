import { motion } from "framer-motion";
import { PageHeader } from "@/components/layout";
import { StatCard } from "@/components/ui/StatCard";

export function SimulatorPage() {
  return (
    <div className="container-main page-section">
      <PageHeader title="Tournament Simulator" subtitle="Monte Carlo simulation of the FIFA World Cup 2026 bracket" badge="Simulation Engine"
        actions={<button className="px-6 py-2.5 rounded-md bg-fifa-navy text-white font-display font-semibold text-body-sm hover:bg-fifa-blue transition-colors">Run Simulation</button>} />
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="card-surface p-6 mb-6">
        <div className="flex flex-wrap items-center gap-6">
          <div><label className="text-caption text-text-tertiary uppercase tracking-wider block mb-1.5">Iterations</label>
            <select className="px-4 py-2.5 rounded-md bg-surface-secondary border border-surface-border text-body-sm"><option>10,000</option><option>50,000</option></select></div>
          <div><label className="text-caption text-text-tertiary uppercase tracking-wider block mb-1.5">Model</label>
            <select className="px-4 py-2.5 rounded-md bg-surface-secondary border border-surface-border text-body-sm"><option>Hybrid</option><option>Elo + Poisson</option></select></div>
        </div>
      </motion.div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {[{ n: "Argentina", f: "🇦🇷", p: "14.2%" }, { n: "France", f: "🇫🇷", p: "12.8%" }, { n: "Brazil", f: "🇧🇷", p: "11.5%" }, { n: "England", f: "🏴󠁧󠁢󠁥󠁮󠁧󠁿", p: "9.7%" }].map((t, i) => (
          <motion.div key={t.n} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}>
            <StatCard label={`${t.f} ${t.n}`} value={t.p} subValue={`#${i + 1} Favourite`} variant={i === 0 ? "highlight" : "default"} />
          </motion.div>
        ))}
      </div>
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="card-surface p-8">
        <h3 className="font-display text-heading-lg text-text-primary mb-6">Tournament Bracket</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {["Group Stage", "Round of 16", "Quarter-Finals", "Semi → Final"].map((s) => (
            <div key={s}><h4 className="text-caption text-text-tertiary uppercase tracking-wider border-b border-surface-border pb-2 mb-3">{s}</h4>
              {[1, 2, 3, 4].map((j) => (<div key={j} className="bg-surface-secondary rounded-md p-3 mb-2"><div className="h-3 bg-surface-tertiary rounded shimmer w-3/4 mb-1.5" /><div className="h-2.5 bg-surface-tertiary rounded shimmer w-1/2" /></div>))}
            </div>
          ))}
        </div>
        <p className="text-body-sm text-text-tertiary mt-6 text-center">Run a simulation to populate the bracket</p>
      </motion.div>
    </div>
  );
}
