interface ConfirmDialogProps {
  isOpen: boolean
  title: string
  description: string
  confirmLabel?: string
  cancelLabel?: string
  danger?: boolean
  onConfirm: () => void
  onCancel: () => void
}

export function ConfirmDialog({
  isOpen,
  title,
  description,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  danger = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  if (!isOpen) return null

  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 100, display: 'grid', placeItems: 'center', padding: 20 }}>
      <button
        type="button"
        aria-label="Close confirmation dialog"
        onClick={onCancel}
        style={{ position: 'absolute', inset: 0, border: 'none', background: 'rgba(0,0,0,0.6)', cursor: 'pointer' }}
      />

      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-dialog-title"
        aria-describedby="confirm-dialog-description"
        style={{
          position: 'relative',
          zIndex: 1,
          width: 'min(100%, 460px)',
          background: 'rgba(10,18,34,0.96)',
          backdropFilter: 'blur(18px)',
          WebkitBackdropFilter: 'blur(18px)',
          border: '1px solid rgba(255,255,255,0.12)',
          borderRadius: 18,
          padding: 24,
          boxShadow: '0 24px 80px rgba(0,0,0,0.5)',
          animation: 'dialogEnter 0.16s ease both',
        }}
      >
        <div style={{ display: 'flex', gap: 14, alignItems: 'flex-start' }}>
          <div style={{ fontSize: 28, lineHeight: 1 }} aria-hidden="true">{danger ? '⚠️' : '❓'}</div>
          <div style={{ display: 'grid', gap: 8, flex: 1 }}>
            <div id="confirm-dialog-title" style={{ fontSize: 20, fontWeight: 800, color: '#fff', fontFamily: 'var(--font-ui)' }}>
              {title}
            </div>
            <div id="confirm-dialog-description" style={{ fontSize: 13, lineHeight: 1.6, color: 'var(--color-text-secondary)' }}>
              {description}
            </div>

            <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end', marginTop: 8, flexWrap: 'wrap' }}>
              <button
                type="button"
                onClick={onCancel}
                style={{
                  minHeight: 40,
                  padding: '0 14px',
                  borderRadius: 10,
                  border: '1px solid rgba(255,255,255,0.12)',
                  background: 'rgba(255,255,255,0.05)',
                  color: '#fff',
                  fontFamily: 'var(--font-ui)',
                  fontSize: 14,
                  fontWeight: 700,
                  cursor: 'pointer',
                }}
              >
                {cancelLabel}
              </button>
              <button
                type="button"
                onClick={onConfirm}
                style={{
                  minHeight: 40,
                  padding: '0 14px',
                  borderRadius: 10,
                  border: danger ? '1px solid rgba(239,68,68,0.35)' : '1px solid rgba(212,175,55,0.55)',
                  background: danger ? 'rgba(239,68,68,0.18)' : 'linear-gradient(180deg, #d9b74e 0%, #c79d24 100%)',
                  color: danger ? '#fecaca' : '#111827',
                  fontFamily: 'var(--font-ui)',
                  fontSize: 14,
                  fontWeight: 800,
                  cursor: 'pointer',
                }}
              >
                {confirmLabel}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}