import { useToastStore } from '@/store/toastStore'

const COLORS: Record<string, { bg: string; border: string; icon: string }> = {
  success: { bg: 'rgba(34,197,94,0.12)', border: 'rgba(34,197,94,0.3)', icon: '✅' },
  error: { bg: 'rgba(239,68,68,0.12)', border: 'rgba(239,68,68,0.3)', icon: '❌' },
  warning: { bg: 'rgba(245,158,11,0.12)', border: 'rgba(245,158,11,0.3)', icon: '⚠️' },
  info: { bg: 'rgba(59,130,246,0.12)', border: 'rgba(59,130,246,0.3)', icon: 'ℹ️' },
}

export function ToastContainer() {
  const { toasts, remove } = useToastStore()

  if (toasts.length === 0) return null

  return (
    <div
      aria-live="polite"
      aria-atomic="true"
      style={{
        position: 'fixed',
        right: 20,
        bottom: 20,
        zIndex: 80,
        display: 'grid',
        gap: 10,
        pointerEvents: 'none',
        width: 'min(360px, calc(100vw - 40px))',
      }}
    >
      {toasts.map((toast) => {
        const c = COLORS[toast.type] || COLORS.info || { bg: 'rgba(59,130,246,0.12)', border: 'rgba(59,130,246,0.3)', icon: 'ℹ️' }

        return (
          <button
            key={toast.id}
            type="button"
            onClick={() => remove(toast.id)}
            style={{
              background: c.bg,
              backdropFilter: 'blur(20px)',
              WebkitBackdropFilter: 'blur(20px)',
              border: `1px solid ${c.border}`,
              borderLeft: `3px solid ${c.border}`,
              borderRadius: 10,
              padding: '12px 16px',
              display: 'flex',
              alignItems: 'flex-start',
              gap: 10,
              cursor: 'pointer',
              pointerEvents: 'all',
              boxShadow: '0 4px 24px rgba(0,0,0,0.4)',
              animation: 'slideInRight 0.2s ease',
              color: '#fff',
              textAlign: 'left',
            }}
            title="Click to dismiss"
          >
            <span aria-hidden="true">{c.icon}</span>
            <span style={{ fontSize: 13, lineHeight: 1.45, color: '#fff' }}>{toast.message}</span>
          </button>
        )
      })}
    </div>
  )
}