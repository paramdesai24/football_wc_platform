import { motion } from "framer-motion";
import { PageHeader } from "@/components/layout";
import { MatchCard } from "@/components/cards/MatchCard";

const matches = [
  { home: "Brazil", away: "Morocco", hf: "🇧🇷", af: "🇲🇦", time: "21:00", s: "Group Stage", g: "Group C", v: "MetLife Stadium", p: { homeWin: 45, draw: 28, awayWin: 27 } },
  { home: "Japan", away: "Spain", hf: "🇯🇵", af: "🇪🇸", time: "18:00", s: "Group Stage", g: "Group F", v: "AT&T Stadium", p: { homeWin: 22, draw: 30, awayWin: 48 } },
  { home: "USA", away: "England", hf: "🇺🇸", af: "🏴󠁧󠁢󠁥󠁮󠁧󠁿", time: "15:00", s: "Group Stage", g: "Group B", v: "Rose Bowl", p: { homeWin: 30, draw: 32, awayWin: 38 } },
  { home: "Germany", away: "Netherlands", hf: "🇩🇪", af: "🇳🇱", time: "21:00", s: "Group Stage", g: "Group E", v: "BMO Field", p: { homeWin: 35, draw: 30, awayWin: 35 } },
];

export function PredictionsPage() {
  return (
    <div className="container-main page-section">
      <PageHeader title="Predictions Dashboard" subtitle="AI-powered predictions for upcoming FIFA World Cup 2026 fixtures" badge="AI Predictions" />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {matches.map((m, i) => (
          <motion.div key={`${m.home}-${m.away}`} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }}>
            <MatchCard homeTeam={m.home} awayTeam={m.away} homeFlag={m.hf} awayFlag={m.af} time={m.time} stage={m.s} group={m.g} venue={m.v} prediction={m.p} />
          </motion.div>
        ))}
      </div>
    </div>
  );
}
