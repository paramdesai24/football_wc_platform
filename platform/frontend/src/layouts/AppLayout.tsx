import { Outlet, useLocation } from "react-router-dom";
import { TopNavBar } from "@/components/layout/TopNavBar";
import { ToastContainer } from "@/components/ui/ToastContainer";
import { PageWrapper } from "@/components/layout/PageWrapper";

export function AppLayout() {
  const { pathname } = useLocation();
  const isAuctionRoom = pathname.startsWith('/auction/room');

  return (
    <div className="wc-app-shell">
      <div className="wc-background" aria-hidden="true" />
      <div className="wc-shell-content" style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
        <TopNavBar />
        <main style={{ flex: 1, paddingBottom: isAuctionRoom ? 0 : 28 }}>
          <PageWrapper>
            <Outlet />
          </PageWrapper>
        </main>
        <ToastContainer />
        {!isAuctionRoom && (
          <footer
            className="wc-footer"
            style={{
              display:        'flex',
              justifyContent: 'space-between',
              alignItems:     'center',
              padding:        '16px 20px',
              fontSize:       '0.75rem',
              borderTop:      '1px solid rgba(255,255,255,0.06)',
              background:     'rgba(5, 13, 26, 0.4)',
              flexWrap:       'wrap',
              gap:            12,
            }}
          >
            {/* Left — branding */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'rgba(255,255,255,0.6)' }}>
              <img
                src="/worldcup_icon.webp"
                alt=""
                width={16}
                height={16}
                style={{ objectFit: 'contain' }}
                onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
              />
              <span style={{ fontWeight: 600, color: '#fff' }}>
                FC Analytics
              </span>
              ·
              <span style={{ color: 'rgba(255,255,255,0.4)' }}>
                live football intelligence · broadcast-ready runtime
              </span>
            </div>

            {/* Right — built by */}
            <div style={{ color: 'rgba(255,255,255,0.4)', fontWeight: 500 }}>
              Built by{' '}
              <span style={{ color: '#d4af37', fontWeight: 600 }}>
                Param Desai
              </span>
            </div>
          </footer>
        )}
      </div>
    </div>
  );
}
