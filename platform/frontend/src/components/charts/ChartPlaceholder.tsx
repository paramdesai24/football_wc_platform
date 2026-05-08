export function ChartPlaceholder({ title, height = "h-64", description }: { title: string; height?: string; description?: string }) {
  return (
    <div className={`card-surface p-6 ${height} flex flex-col items-center justify-center`}>
      <div className="w-12 h-12 rounded-full bg-surface-tertiary flex items-center justify-center mb-3">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-text-tertiary">
          <path d="M3 3v18h18" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M7 16l4-8 4 4 4-6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
      <h4 className="font-display text-heading-sm text-text-secondary mb-1">{title}</h4>
      {description && <p className="text-caption text-text-tertiary text-center max-w-xs">{description}</p>}
    </div>
  );
}
