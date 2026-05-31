interface EmptyStateProps {
  icon: string
  title: string
  description: string
  action?: {
    label: string
    onClick: () => void
  }
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div
      style={{
        background: 'rgba(10,18,34,0.72)',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        border: '1px solid rgba(255,255,255,0.09)',
        borderRadius: 16,
        padding: 28,
        display: 'grid',
        gap: 12,
        placeItems: 'center',
        textAlign: 'center',
      }}
    >
      <div style={{ fontSize: 36, lineHeight: 1 }} aria-hidden="true">{icon}</div>
      <div style={{ display: 'grid', gap: 6, maxWidth: 520 }}>
        <div style={{ fontSize: 20, fontWeight: 800, color: '#fff', fontFamily: 'var(--font-ui)' }}>{title}</div>
        <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>{description}</div>
      </div>
      {action && (
        <button
          type="button"
          onClick={action.onClick}
          style={{
            minHeight: 42,
            padding: '0 16px',
            borderRadius: 12,
            border: '1px solid rgba(212,175,55,0.55)',
            background: 'linear-gradient(180deg, #d9b74e 0%, #c79d24 100%)',
            color: '#111827',
            fontFamily: 'var(--font-ui)',
            fontSize: 14,
            fontWeight: 800,
            cursor: 'pointer',
          }}
        >
          {action.label}
        </button>
      )}
    </div>
  )
}