import { FlagImg } from "@/components/FlagImg";

interface MatchCardProps {
  homeTeam: string;
  awayTeam: string;
  homeFlag?: string;
  awayFlag?: string;
  time?: string;
  homeScore?: number;
  awayScore?: number;
  stage?: string;
  group?: string;
  venue?: string;
  prediction?: { homeWin: number; draw: number; awayWin: number };
}

export function MatchCard({ homeTeam, awayTeam, homeFlag, awayFlag, time, homeScore, awayScore, stage, group, venue, prediction }: MatchCardProps) {
  const hasScore = homeScore !== undefined && awayScore !== undefined;
  return (
    <div className="card-surface p-5 hover:shadow-[0_4px_12px_rgba(26,42,68,0.08)] transition-shadow">
      <div className="flex items-center justify-center gap-8">
        <div className="flex-1 text-right">
          <div className="flex items-center justify-end gap-3">
            <span className="font-display text-heading-md text-text-primary">{homeTeam}</span>
            {homeFlag && <FlagImg code={homeFlag} size={24} />}
          </div>
        </div>
        <div className="flex-shrink-0 w-24 text-center">
          {hasScore ? (
            <div className="font-display text-display-sm text-text-primary">{homeScore} – {awayScore}</div>
          ) : time ? (
            <div className="font-display text-display-sm text-text-secondary">{time}</div>
          ) : (
            <div className="text-body-sm text-text-tertiary">vs</div>
          )}
        </div>
        <div className="flex-1 text-left">
          <div className="flex items-center gap-3">
            {awayFlag && <FlagImg code={awayFlag} size={24} />}
            <span className="font-display text-heading-md text-text-primary">{awayTeam}</span>
          </div>
        </div>
      </div>
      <div className="flex items-center justify-center gap-2 mt-3 text-caption text-text-tertiary">
        {stage && <span>{stage}</span>}
        {stage && group && <span>·</span>}
        {group && <span>{group}</span>}
        {(stage || group) && venue && <span>·</span>}
        {venue && <span>{venue}</span>}
      </div>
      {prediction && (
        <div className="mt-4 pt-4 border-t border-surface-border">
          <div className="flex items-center gap-1 h-2 rounded-full overflow-hidden">
            <div className="h-full bg-fifa-blue rounded-l-full" style={{ width: `${prediction.homeWin}%` }} />
            <div className="h-full bg-surface-muted" style={{ width: `${prediction.draw}%` }} />
            <div className="h-full bg-fifa-sky rounded-r-full" style={{ width: `${prediction.awayWin}%` }} />
          </div>
          <div className="flex items-center justify-between mt-2 text-caption">
            <span className="text-fifa-blue font-semibold">{prediction.homeWin}%</span>
            <span className="text-text-tertiary">{prediction.draw}%</span>
            <span className="text-fifa-sky font-semibold">{prediction.awayWin}%</span>
          </div>
        </div>
      )}
    </div>
  );
}
