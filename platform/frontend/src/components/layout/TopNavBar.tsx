import { useEffect, useMemo, useRef, useState } from "react";
import { NavLink } from "react-router-dom";
import { NAV_ITEMS } from "@/routes/constants";
import useAuthStore from '@/store/authStore'
import { ChevronDown, LogOut } from 'lucide-react'

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

export function TopNavBar() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const user = useAuthStore((s) => s.user)
  const signOut = useAuthStore((s) => s.signOut)
  const userMenuRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      const nav = document.querySelector('.navbar');
      if (nav && !nav.contains(e.target as Node)) {
        setMenuOpen(false);
        setUserMenuOpen(false)
      }
    };

    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const userDisplay = useMemo(() => {
    if (!user) {
      return ''
    }

    return user.username ?? user.email ?? user.id.slice(0, 6)
  }, [user])

  const userInitial = useMemo(() => {
    if (!userDisplay) {
      return '?'
    }

    return userDisplay.trim().charAt(0).toUpperCase()
  }, [userDisplay])

  async function handleSignOut() {
    setUserMenuOpen(false)
    await signOut()
  }

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
              className={({ isActive }) => `nav-link${item.path === "/play-as-team" ? " nav-link-cta" : ""}${item.path === "/about" ? " nav-link-cta nav-link-about" : ""}${isActive ? " active" : ""}`}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          {user ? (
            <div ref={userMenuRef} style={{ position: 'relative' }}>
              <button
                type="button"
                onClick={() => setUserMenuOpen((open) => !open)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  background: 'rgba(212,175,55,0.1)',
                  border: '1px solid rgba(212,175,55,0.2)',
                  borderRadius: '20px',
                  padding: '6px 14px 6px 8px',
                  cursor: 'pointer',
                  color: '#fff',
                }}
              >
                <div style={{ width: 28, height: 28, borderRadius: '999px', background: '#d4af37', color: '#0a0f1a', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '12px', fontWeight: 800 }}>
                  {userInitial}
                </div>
                <span style={{ fontSize: '13px', color: '#fff' }}>{userDisplay}</span>
                <ChevronDown size={14} color="rgba(255,255,255,0.75)" />
              </button>

              {userMenuOpen && (
                <div style={{ position: 'absolute', right: 0, top: 'calc(100% + 10px)', minWidth: 160, background: 'rgba(10,18,34,0.96)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 14, boxShadow: '0 18px 40px rgba(0,0,0,0.42)', padding: 8, zIndex: 60 }}>
                  <button
                    type="button"
                    onClick={handleSignOut}
                    style={{ display: 'flex', alignItems: 'center', gap: 10, width: '100%', border: 'none', background: 'rgba(248,113,113,0.08)', color: '#f87171', borderRadius: 10, padding: '10px 12px', cursor: 'pointer', textAlign: 'left' }}
                  >
                    <LogOut size={14} />
                    Log out
                  </button>
                </div>
              )}
            </div>
          ) : (
            <NavLink to="/auth" style={{ cursor: 'pointer' }}>Sign in</NavLink>
          )}
        </div>
      </div>

    </header>
  );
}
