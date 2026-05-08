import { motion } from "framer-motion";
import { PageHeader } from "@/components/layout";

export function PredictorPage() {
  return (
    <div className="container-main page-section">
      <PageHeader title="Match Predictor" subtitle="Select two teams to generate AI-powered match predictions using Elo, Poisson, and XGBoost models" badge="Prediction Engine" />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="card-surface p-8">
            <div className="flex items-center justify-center gap-8">
              <div className="flex-1 text-center">
                <div className="w-24 h-24 mx-auto rounded-full bg-surface-tertiary flex items-center justify-center mb-4 border-2 border-dashed border-surface-border"><span className="text-4xl">🏠</span></div>
                <h3 className="font-display text-heading-md text-text-primary mb-2">Home Team</h3>
                <button className="w-full px-4 py-3 rounded-md bg-surface-secondary border border-surface-border text-body-md text-text-secondary hover:border-fifa-blue transition-colors">Select country…</button>
              </div>
              <div className="flex flex-col items-center gap-3">
                <div className="w-14 h-14 rounded-full bg-fifa-navy flex items-center justify-center"><span className="font-display text-white font-bold text-body-lg">VS</span></div>
                <button className="text-caption text-fifa-blue hover:text-fifa-navy transition-colors font-medium">⇆ Swap</button>
              </div>
              <div className="flex-1 text-center">
                <div className="w-24 h-24 mx-auto rounded-full bg-surface-tertiary flex items-center justify-center mb-4 border-2 border-dashed border-surface-border"><span className="text-4xl">✈️</span></div>
                <h3 className="font-display text-heading-md text-text-primary mb-2">Away Team</h3>
                <button className="w-full px-4 py-3 rounded-md bg-surface-secondary border border-surface-border text-body-md text-text-secondary hover:border-fifa-blue transition-colors">Select country…</button>
              </div>
            </div>
            <div className="mt-8 pt-6 border-t border-surface-border text-center">
              <button className="px-8 py-3 rounded-md bg-fifa-navy text-white font-display font-semibold text-body-md hover:bg-fifa-blue transition-colors">Generate Prediction</button>
            </div>
          </motion.div>
        </div>
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="card-surface p-6">
          <h3 className="font-display text-heading-md text-text-primary mb-4">Prediction Result</h3>
          <div className="text-center py-12">
            <div className="w-16 h-16 mx-auto rounded-full bg-surface-tertiary flex items-center justify-center mb-4"><span className="text-2xl">📊</span></div>
            <p className="text-body-sm text-text-tertiary">Select both teams and click predict to generate match analysis</p>
          </div>
          <div className="space-y-3 mt-6 pt-6 border-t border-surface-border">
            <h4 className="text-caption text-text-tertiary uppercase tracking-wider">Model Components</h4>
            {["Elo Rating Comparison", "Poisson Goal Distribution", "XGBoost Match Outcome", "Form Analysis"].map((m) => (
              <div key={m} className="flex items-center gap-3 py-2"><div className="w-2 h-2 rounded-full bg-surface-muted" /><span className="text-body-sm text-text-secondary">{m}</span></div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
