import { useAuctionStore } from '@/store/auctionStore'

export function ReconnectionBanner() {
  const status = useAuctionStore((state) => state.connectionStatus)

  if (status === 'connected') return null

  const isReconnecting = status === 'reconnecting'

  return (
    <div
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 30,
        marginBottom: 14,
        background: isReconnecting ? 'rgba(14, 31, 48, 0.94)' : 'rgba(48, 17, 22, 0.94)',
        borderBottom: isReconnecting ? '1px solid rgba(59,130,246,0.28)' : '1px solid rgba(239,68,68,0.28)',
        boxShadow: '0 10px 28px rgba(0,0,0,0.24)',
        backdropFilter: 'blur(14px)',
        WebkitBackdropFilter: 'blur(14px)',
        animation: 'slideDown 0.18s ease both',
      }}
    >
      <div style={{ maxWidth: 1400, margin: '0 auto', padding: '10px 20px', display: 'flex', alignItems: 'center', gap: 10, fontSize: 13, fontWeight: 700, color: '#fff' }}>
        <span aria-hidden="true">{isReconnecting ? '🔄' : '❌'}</span>
        <span>{isReconnecting ? 'Connection lost — reconnecting to auction room...' : 'Disconnected — check your internet connection'}</span>
      </div>
    </div>
  )
}