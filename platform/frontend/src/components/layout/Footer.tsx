export function Footer() {
  const year = new Date().getFullYear();
  return (
    <footer className="bg-fifa-navy text-white mt-auto">
      <div className="container-main py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="md:col-span-1">
            <div className="flex items-center gap-2 mb-4">
              <span className="text-xl">⚽</span>
              <div>
                <h3 className="font-display font-bold text-sm tracking-wide">FIFA WC 2026™</h3>
                <p className="text-white/40 text-[10px] tracking-widest uppercase">Intelligence</p>
              </div>
            </div>
            <p className="text-white/50 text-body-sm leading-relaxed">
              Advanced football intelligence, match prediction, and tournament simulation powered by data science.
            </p>
          </div>
          {[
            { title: "Platform", items: ["Rankings", "Match Predictor", "Simulator", "Player Analytics", "Team Analytics"] },
            { title: "Intelligence", items: ["Elo Ratings", "Poisson Models", "XGBoost Predictions", "Monte Carlo", "Form Analysis"] },
            { title: "Data", items: ["Historical Results", "Player Statistics", "Transfer Values", "Current Form", "Tournament Data"] },
          ].map((col) => (
            <div key={col.title}>
              <h4 className="font-display font-semibold text-body-sm mb-4 text-white/80 uppercase tracking-wider">{col.title}</h4>
              <ul className="space-y-2.5">
                {col.items.map((item) => (
                  <li key={item}><span className="text-white/50 text-body-sm hover:text-white/80 transition-colors cursor-pointer">{item}</span></li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="section-divider mt-8 mb-6 opacity-20" />
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-white/30 text-caption">© {year} FIFA World Cup 2026™ Intelligence Platform. Research & educational purposes.</p>
          <span className="text-white/30 text-caption">Built with React + Vite + FastAPI + ML</span>
        </div>
      </div>
    </footer>
  );
}
