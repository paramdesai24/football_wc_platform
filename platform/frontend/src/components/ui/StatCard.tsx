import type { ReactNode } from "react";

interface StatCardProps {
  label: string;
  value: string | number;
  icon?: ReactNode;
  trend?: string;
  highlight?: boolean;
}

export function StatCard({ label, value, icon, trend, highlight }: StatCardProps) {
  return (
    <div className={`card p-5 ${highlight ? "border-t-2 border-t-[#003DA5]" : ""}`}>
      <div className="flex items-center justify-between mb-3">
        {icon && <span className="text-[#003DA5]">{icon}</span>}
        <span className="text-caption text-text-muted">{label}</span>
      </div>
      <div className="text-stat text-text-primary">{value}</div>
      {trend && (
        <div className={`text-xs mt-1 font-mono ${
          trend.startsWith("+") ? "text-[#059669]" : trend.startsWith("-") ? "text-[#E11D48]" : "text-text-muted"
        }`}>{trend}</div>
      )}
    </div>
  );
}
