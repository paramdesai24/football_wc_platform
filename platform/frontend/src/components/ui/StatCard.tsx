import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface StatCardProps {
  label: string;
  value: string | number;
  subValue?: string;
  trend?: "up" | "down" | "stable";
  trendValue?: string;
  variant?: "default" | "highlight" | "compact";
}

export function StatCard({ label, value, subValue, trend, trendValue, variant = "default" }: StatCardProps) {
  return (
    <div className={cn("card-surface", variant === "highlight" ? "p-5 border-l-4 border-l-fifa-blue" : "p-5")}>
      <span className="text-caption text-text-tertiary uppercase tracking-wider block mb-3">{label}</span>
      <div className="flex items-end gap-2">
        <span className={cn("stat-value text-text-primary", variant === "compact" ? "text-stat-sm" : "text-stat")}>{value}</span>
        {trend && trendValue && (
          <span className={cn("text-caption font-semibold mb-1", trend === "up" && "text-status-win", trend === "down" && "text-status-loss", trend === "stable" && "text-text-tertiary")}>
            {trend === "up" ? "↑" : trend === "down" ? "↓" : "→"} {trendValue}
          </span>
        )}
      </div>
      {subValue && <p className="text-body-sm text-text-secondary mt-1">{subValue}</p>}
    </div>
  );
}

export function StatRow({ label, value, maxValue = 100, barColor = "bg-fifa-blue" }: { label: string; value: number; maxValue?: number; barColor?: string }) {
  const pct = (value / maxValue) * 100;
  return (
    <div className="flex items-center gap-4 py-2">
      <span className="text-body-sm text-text-secondary w-32 flex-shrink-0">{label}</span>
      <div className="flex-1 h-2 bg-surface-tertiary rounded-full overflow-hidden">
        <motion.div initial={{ width: 0 }} animate={{ width: `${pct}%` }} transition={{ duration: 0.6, delay: 0.1 }} className={cn("h-full rounded-full", barColor)} />
      </div>
      <span className="stat-value text-body-sm text-text-primary w-12 text-right">{value}</span>
    </div>
  );
}
