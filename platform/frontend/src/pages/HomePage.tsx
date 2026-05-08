import { motion } from "framer-motion";
import { StatCard } from "@/components/ui/StatCard";
import { MatchCard } from "@/components/cards/MatchCard";
import { PlayerCard } from "@/components/cards/PlayerCard";
import { SectionHeader } from "@/components/layout/Section";

const stagger = { hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.06 } } };
const fadeUp = { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0, transition: { duration: 0.4 } } };

export function HomePage() {
  return (
    <>
      {/* Hero */}
      <section className="bg-gradient-hero text-white relative overflow-hidden">
        <div className="container-main relative z-10 py-16 md:py-24">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }} className="max-w-3xl">
            <div className="inline-flex items-center gap-2 bg-white/10 rounded-full px-4 py-1.5 mb-6">
              <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
              <span className="text-caption text-white/80">FIFA World Cup 2026™ · United States, Mexico & Canada</span>
            </div>
            <h1 className="font-display text-display-xl text-white mb-4 leading-tight">
              Football Intelligence<br /><span className="text-fifa-light">& Prediction Platform</span>
            </h1>
            <p className="text-body-lg text-white/60 max-w-xl leading-relaxed">
              Advanced analytics ecosystem powered by Elo ratings, Poisson models, XGBoost predictions, and Monte Carlo tournament simulation.
            </p>
          </motion.div>
        </div>
        <div className="h-12 bg-gradient-to-b from-transparent to-surface-secondary" />
      </section>

      {/* Metrics */}
      <section className="container-main -mt-6 relative z-20">
        <motion.div variants={stagger} initial="hidden" animate="show" className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: "Qualified Teams", value: "48", sub: "Expanded format", v: "highlight" as const },
            { label: "Host Nations", value: "3", sub: "USA · Mexico · Canada" },
            { label: "Total Matches", value: "104", sub: "Group & Knockout stages" },
            { label: "Match Venues", value: "16", sub: "Across North America" },
          ].map((s) => (
            <motion.div key={s.label} variants={fadeUp}><StatCard label={s.label} value={s.value} subValue={s.sub} variant={s.v || "default"} /></motion.div>
          ))}
        </motion.div>
      </section>

      {/* Featured Predictions */}
      <section className="container-main page-section">
        <SectionHeader title="Featured Predictions" subtitle="AI-powered match predictions for upcoming World Cup fixtures" />
        <motion.div variants={stagger} initial="hidden" animate="show" className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {[
            { home: "Brazil", away: "Germany", hf: "🇧🇷", af: "🇩🇪", s: "Group Stage", g: "Group E", v: "MetLife Stadium", p: { homeWin: 42, draw: 28, awayWin: 30 } },
            { home: "Argentina", away: "France", hf: "🇦🇷", af: "🇫🇷", s: "Group Stage", g: "Group A", v: "SoFi Stadium", p: { homeWin: 38, draw: 30, awayWin: 32 } },
            { home: "Spain", away: "England", hf: "🇪🇸", af: "🏴󠁧󠁢󠁥󠁮󠁧󠁿", s: "Group Stage", g: "Group C", v: "AT&T Stadium", p: { homeWin: 40, draw: 32, awayWin: 28 } },
            { home: "USA", away: "Mexico", hf: "🇺🇸", af: "🇲🇽", s: "Group Stage", g: "Group B", v: "Azteca Stadium", p: { homeWin: 36, draw: 30, awayWin: 34 } },
          ].map((m) => (
            <motion.div key={`${m.home}-${m.away}`} variants={fadeUp}>
              <MatchCard homeTeam={m.home} awayTeam={m.away} homeFlag={m.hf} awayFlag={m.af} stage={m.s} group={m.g} venue={m.v} prediction={m.p} />
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* Top Players */}
      <section className="container-main page-section pt-0">
        <SectionHeader title="Top Form Players" subtitle="Highest current form scores based on 2025/26 season data" />
        <motion.div variants={stagger} initial="hidden" animate="show" className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { surname: "MBAPPÉ", firstName: "Kylian", country: "France", flag: "🇫🇷", pos: "FWD", form: 94, metrics: [{ label: "Goals", value: 28 }, { label: "Assists", value: 11 }] },
            { surname: "HAALAND", firstName: "Erling", country: "Norway", flag: "🇳🇴", pos: "FWD", form: 92, metrics: [{ label: "Goals", value: 34 }, { label: "Assists", value: 7 }] },
            { surname: "BELLINGHAM", firstName: "Jude", country: "England", flag: "🏴󠁧󠁢󠁥󠁮󠁧󠁿", pos: "MID", form: 91, metrics: [{ label: "Goals", value: 16 }, { label: "Assists", value: 14 }] },
            { surname: "VINÍCIUS JR", firstName: "Vinícius", country: "Brazil", flag: "🇧🇷", pos: "FWD", form: 90, metrics: [{ label: "Goals", value: 22 }, { label: "Assists", value: 13 }] },
          ].map((p, i) => (
            <motion.div key={p.surname} variants={fadeUp}>
              <PlayerCard surname={p.surname} firstName={p.firstName} country={p.country} countryFlag={p.flag} position={p.pos} formScore={p.form} rank={i + 1} metrics={p.metrics} />
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* Intelligence Modules */}
      <section className="bg-white border-t border-surface-border">
        <div className="container-main page-section">
          <SectionHeader title="Intelligence Modules" subtitle="Core analytical capabilities powering the prediction ecosystem" />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[
              { title: "Elo Rating Engine", desc: "Dynamic team strength ratings incorporating historical performance, home advantage, and recency weighting.", tag: "Team Strength" },
              { title: "Poisson Goal Model", desc: "Statistical goal distribution modeling for accurate scoreline predictions based on attack and defense metrics.", tag: "Scoring" },
              { title: "XGBoost Predictor", desc: "Gradient-boosted match outcome predictions using engineered features from multiple data sources.", tag: "Prediction" },
              { title: "Monte Carlo Simulation", desc: "10,000+ iteration tournament simulations generating probabilistic outcomes for every team.", tag: "Simulation" },
              { title: "Player Form Analysis", desc: "Current season form scoring using goals, assists, minutes, and match ratings from top leagues.", tag: "Intelligence" },
              { title: "Squad Strength Index", desc: "Aggregate squad quality metrics combining individual player form, depth, and positional coverage.", tag: "Analytics" },
            ].map((f) => (
              <motion.div key={f.title} whileHover={{ y: -2 }} className="card-surface p-6 group">
                <span className="badge badge-fifa text-[11px] mb-3 inline-block">{f.tag}</span>
                <h3 className="font-display text-heading-md text-text-primary mb-2 group-hover:text-fifa-blue transition-colors">{f.title}</h3>
                <p className="text-body-sm text-text-secondary leading-relaxed">{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
