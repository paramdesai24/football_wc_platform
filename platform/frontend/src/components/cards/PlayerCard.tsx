import { motion } from "framer-motion";
import { cn, getFormBgColor, getPositionColor } from "@/lib/utils";
import { FlagImg } from "@/components/FlagImg";

interface PlayerCardProps {
  surname: string;
  firstName?: string;
  country: string;
  countryFlag?: string;
  position: string;
  formScore: number;
  metrics?: { label: string; value: string | number }[];
  rank?: number;
  onClick?: () => void;
}

export function PlayerCard({ surname, firstName, country, countryFlag, position, formScore, metrics = [], rank, onClick }: PlayerCardProps) {
  return (
    <motion.div whileHover={{ y: -2 }} transition={{ duration: 0.15 }} onClick={onClick} className="card-surface p-5 cursor-pointer group relative overflow-hidden">
      {rank && (
        <div className="absolute top-3 right-3 w-7 h-7 rounded-full bg-surface-tertiary flex items-center justify-center">
          <span className="text-caption text-text-tertiary font-bold">{rank}</span>
        </div>
      )}
      <div className="flex items-center gap-3 mb-4">
        <span className={cn("badge text-[11px]", getPositionColor(position))}>{position}</span>
        <span className={cn("badge text-[11px]", getFormBgColor(formScore))}>Form {formScore}</span>
      </div>
      <div className="mb-4">
        {firstName && <p className="text-caption text-text-tertiary uppercase tracking-wider mb-0.5">{firstName}</p>}
        <h3 className="font-display text-heading-lg text-text-primary uppercase tracking-wide group-hover:text-fifa-blue transition-colors">{surname}</h3>
      </div>
      <div className="flex items-center gap-2 mb-4 pb-4 border-b border-surface-border">
        {countryFlag && <FlagImg code={countryFlag} size={18} />}
        <span className="text-body-sm text-text-secondary">{country}</span>
      </div>
      {metrics.length > 0 && (
        <div className="grid grid-cols-2 gap-3">
          {metrics.map((m) => (
            <div key={m.label}>
              <p className="text-[11px] text-text-tertiary uppercase tracking-wider mb-0.5">{m.label}</p>
              <p className="stat-value text-stat-sm text-text-primary">{m.value}</p>
            </div>
          ))}
        </div>
      )}
    </motion.div>
  );
}
