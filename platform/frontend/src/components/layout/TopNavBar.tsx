import { useEffect, useRef, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { NAV_ITEMS } from "@/routes/constants";
import useAuthStore from '@/store/authStore'

function NavIcon() {
  const PRIMARY = "/worldcup_icon.webp";
  const FALLBACK = "https://imgs.search.brave.com/M6EmsapjvWCxIaGgnWVVtsZoHw5_wrlpPi-8hIOVZug/rs:fit:860:0:0:0/g:ce/aHR0cHM6Ly9jZG4u/cHJvZC53ZWJzaXRl/LWZpbGVzLmNvbS82/OGY1NTA5OTI1NzBj/YTAzMjI3MzdkYzIv/NjlmNGE4MmUzNjg1/NzMxYTNhYjUwODZlX2ZpZmEtd29ybGQtY3VwLTIwMjYtb2Zm/aWNpYWwtbG9nby1m/b290eWxvZ29zLXdo/aXRlLnBuZw";
  const [src, setSrc] = useState(PRIMARY);

  useEffect(() => {
    const img = new window.Image();
    img.src = PRIMARY;
    img.onerror = () => setSrc(FALLBACK);
  }, []);

  return (
    <img
      src={src}
      alt=""
      width={32}
      height={32}
      style={{ width: 32, height: 32, objectFit: "contain", flexShrink: 0 }}
      onError={() => setSrc(FALLBACK)}
    />
  );
}

const dropdownItemStyle: React.CSSProperties = {
  display:      'block',
  width:        '100%',
  padding:      '9px 12px',
  background:   'transparent',
  border:       'none',
  borderRadius: 8,
  color:        'rgba(255,255,255,0.75)',
  fontFamily:   'var(--font-ui)',
  fontSize:     13,
  fontWeight:   500,
  cursor:       'pointer',
  textAlign:    'left',
  transition:   'background 0.1s',
}

export function TopNavBar() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const user = useAuthStore((s) => s.user)
  const signOut = useAuthStore((s) => s.signOut)
  const dropdownRef = useRef<HTMLDivElement | null>(null)
  const navigate = useNavigate()

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      const nav = document.querySelector('.navbar');
      if (nav && !nav.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const avatarLetter = (user?.username?.[0] ?? user?.email?.[0] ?? 'U').toUpperCase()

  return (
    <header
      className={`navbar${menuOpen ? " menu-open" : ""}`}
      style={{
        position: "sticky",
        top: 0,
        zIndex: 50,
        background: "rgba(5, 13, 26, 0.82)",
        backdropFilter: "blur(16px)",
        borderBottom: "1px solid rgba(255,255,255,0.08)",
      }}
    >
      <div
        style={{
          maxWidth: 1280,
          margin: "0 auto",
          padding: "0 20px",
          display: "flex",
          gap: 6,
          alignItems: "center",
          justifyContent: "space-between",
          height: 56,
          flexWrap: "nowrap",
        }}
      >
        <NavLink
          to="/"
          className="nav-brand"
          style={{
            display: "flex",
            flexDirection: "row",
            gap: 10,
            lineHeight: 1.1,
            textDecoration: "none",
            alignItems: "center",
          }}
        >
          <NavIcon />
          <span className="nav-brand-name">FC Analytics</span>
        </NavLink>

        <div className="nav-mobile-shell">
          {/* Hamburger button — mobile only */}
          <button
            type="button"
            className={`nav-hamburger${menuOpen ? " open" : ""}`}
            onClick={() => setMenuOpen((open) => !open)}
            aria-label="Toggle menu"
            aria-expanded={menuOpen}
          >
            <span className={`nav-ham-bar${menuOpen ? " open" : ""}`} />
            <span className={`nav-ham-bar${menuOpen ? " open" : ""}`} />
            <span className={`nav-ham-bar${menuOpen ? " open" : ""}`} />
          </button>

          {/* Mobile dropdown menu */}
          {menuOpen && (
            <nav className="nav-mobile-menu">
              {NAV_ITEMS.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  end={item.path === "/"}
                  className={({ isActive }) => `nav-mobile-link${isActive ? " active" : ""}`}
                  onClick={() => setMenuOpen(false)}
                >
                  {item.label}
                </NavLink>
              ))}
            </nav>
          )}
        </div>

        <nav className="nav-links">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === "/"}
              className={({ isActive }) => `nav-link${item.path === "/about" ? " nav-link-cta nav-link-about" : ""}${isActive ? " active" : ""}`}
            >
              {item.label}
            </NavLink>
          ))}
          {!user && (
            <NavLink
              to="/auth"
              className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
              style={{ cursor: 'pointer' }}
            >
              Sign in
            </NavLink>
          )}
        </nav>
        {user && (
          <div ref={dropdownRef} style={{ position: 'relative', zIndex: 60 }}>
            {/* Avatar button — always visible */}
            <button
              onClick={() => setDropdownOpen(o => !o)}
              style={{
                width:          34,
                height:         34,
                borderRadius:   '50%',
                background:     '#d4af37',
                border:         'none',
                color:          '#0a0f1a',
                fontFamily:     'var(--font-ui)',
                fontSize:       13,
                fontWeight:     700,
                cursor:         'pointer',
                display:        'flex',
                alignItems:     'center',
                justifyContent: 'center',
                flexShrink:     0,
              }}
            >
              {avatarLetter}
            </button>

            {/* Dropdown — fixed so it doesn't get clipped */}
            {dropdownOpen && (
              <div style={{
                position:        'absolute',
                right:           0,
                top:             'calc(100% + 8px)',
                width:           240,
                background:      'rgba(10, 18, 34, 0.95)',
                backdropFilter:  'blur(20px)',
                border:          '1px solid rgba(255,255,255,0.08)',
                borderRadius:    12,
                padding:         12,
                boxShadow:       '0 10px 25px rgba(0,0,0,0.5)',
                display:         'flex',
                flexDirection:   'column',
                gap:             8,
              }}>
                {/* User info */}
                <div style={{ padding: '4px 8px', borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: 8, marginBottom: 4 }}>
                  <div style={{ fontWeight: 600, fontSize: 13, color: '#fff', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {user?.username ?? 'User'}
                  </div>
                  <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.45)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {user?.email}
                  </div>
                </div>

                {/* Menu items */}
                <button
                  id="btn-my-auctions"
                  onClick={() => { setDropdownOpen(false); navigate('/my-auctions') }}
                  style={dropdownItemStyle}
                >
                  🏆 My Auctions
                </button>
                <button
                  onClick={() => { setDropdownOpen(false); navigate('/auction') }}
                  style={dropdownItemStyle}
                >
                  🏟 Auction
                </button>
                <button
                  onClick={() => { setDropdownOpen(false); navigate('/auction/info') }}
                  style={dropdownItemStyle}
                >
                  ℹ️ Player Pool
                </button>
                
                <button
                  onClick={() => { setDropdownOpen(false); signOut() }}
                  style={{ ...dropdownItemStyle, color: '#f87171' }}
                >
                  → Log Out
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </header>
  );
}
