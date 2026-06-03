import { useEffect, useState } from 'react'
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import useAuthStore from '@/store/authStore'
import { Eye, EyeOff } from 'lucide-react'

function BrandIcon() {
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
      alt="FC Analytics"
      width={24}
      height={24}
      style={{ width: 24, height: 24, objectFit: "contain", flexShrink: 0 }}
      onError={() => setSrc(FALLBACK)}
    />
  );
}

export default function AuthPage() {
  const init = useAuthStore((s) => s.init)
  const signIn = useAuthStore((s) => s.signIn)
  const signUp = useAuthStore((s) => s.signUp)
  const signInWithGoogle = useAuthStore((s) => s.signInWithGoogle)
  const user = useAuthStore((s) => s.user)
  const error = useAuthStore((s) => s.error)
  const loading = useAuthStore((s) => s.loading)

  const [isSignup, setIsSignup] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [username, setUsername] = useState('')
  const [show, setShow] = useState(false)
  const [hoveredPrimary, setHoveredPrimary] = useState(false)
  const [hoveredGoogle, setHoveredGoogle] = useState(false)
  const [params] = useSearchParams()
  const location = useLocation()
  const navigate = useNavigate()

  useEffect(() => {
    init()
  }, [init])

  useEffect(() => {
    if (user) {
      const redirect = params.get('redirect') || '/'
      navigate(redirect)
    }
  }, [user, navigate, params])

  async function onSubmit(e: any) {
    e.preventDefault()
    if (isSignup) {
      await signUp(email, password, username || undefined)
    } else {
      await signIn(email, password)
    }
  }

  function onGoogleSignIn() {
    localStorage.setItem('auth_redirect', location.state?.from || '/auction')
    void signInWithGoogle(window.location.origin + '/auction')
  }

  const inputBaseStyle = {
    background: 'rgba(255,255,255,0.06)',
    border: '1px solid rgba(255,255,255,0.12)',
    borderRadius: '10px',
    padding: '12px 14px',
    color: '#fff',
    fontSize: '14px',
    width: '100%',
    outline: 'none',
    transition: 'border-color 0.2s',
    boxSizing: 'border-box' as const,
  }

  const labelStyle = {
    fontSize: '12px',
    color: 'rgba(255,255,255,0.5)',
    fontWeight: 500,
    marginBottom: 4,
    display: 'block',
  }

  const pillTabStyle = (active: boolean) => ({
    flex: 1,
    padding: '8px',
    border: 'none',
    borderRadius: '7px',
    background: active ? 'rgba(212,175,55,0.15)' : 'transparent',
    color: active ? '#d4af37' : 'rgba(255,255,255,0.4)',
    fontSize: '13px',
    fontWeight: active ? 600 : 500,
    cursor: 'pointer' as const,
    transition: 'all 0.2s',
  })

  const primaryButtonStyle = {
    padding: '13px',
    background: 'linear-gradient(135deg, #d4af37, #b8962e)',
    border: 'none',
    borderRadius: '10px',
    color: '#0a0f1a',
    fontSize: '14px',
    fontWeight: '700',
    cursor: 'pointer' as const,
    width: '100%',
    transition: 'opacity 0.2s, transform 0.1s',
    letterSpacing: '0.03em',
    opacity: loading ? 0.6 : hoveredPrimary ? 0.9 : 1,
    transform: hoveredPrimary ? 'translateY(-1px)' : 'translateY(0)',
  }

  const googleButtonStyle = {
    padding: '12px',
    background: hoveredGoogle ? 'rgba(255,255,255,0.10)' : 'rgba(255,255,255,0.06)',
    border: `1px solid ${hoveredGoogle ? 'rgba(255,255,255,0.22)' : 'rgba(255,255,255,0.12)'}`,
    borderRadius: '10px',
    color: '#fff',
    fontSize: '14px',
    fontWeight: '500',
    cursor: 'pointer' as const,
    width: '100%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '10px',
    transition: 'background 0.2s, border-color 0.2s',
  }

  const forgotStyle = {
    background: 'none',
    border: 'none',
    color: 'rgba(212,175,55,0.7)',
    fontSize: '12px',
    cursor: 'pointer' as const,
    textAlign: 'right' as const,
    padding: '0',
    textDecoration: 'underline',
    transition: 'color 0.2s',
  }

  const errorStyle = {
    background: 'rgba(239,68,68,0.1)',
    border: '1px solid rgba(239,68,68,0.25)',
    borderRadius: '8px',
    padding: '10px 14px',
    color: '#f87171',
    fontSize: '13px',
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '32px 16px',
      }}
    >
      <div
        style={{
          background: 'rgba(10, 18, 34, 0.85)',
          backdropFilter: 'blur(24px)',
          border: '1px solid rgba(255,255,255,0.08)',
          borderRadius: '20px',
          padding: '40px 44px',
          width: '100%',
          maxWidth: '420px',
          display: 'flex',
          flexDirection: 'column',
          gap: '20px',
          boxShadow: '0 24px 64px rgba(0,0,0,0.5)',
        }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <BrandIcon />
            <div style={{ fontSize: '13px', letterSpacing: '0.15em', fontWeight: 700, color: '#d4af37' }}>
              FC ANALYTICS
            </div>
          </div>
          <h2 style={{ fontSize: '22px', color: '#fff', fontWeight: 700, margin: 0 }}>
            {isSignup ? 'Create account' : 'Welcome back'}
          </h2>
        </div>

        <div style={{ display: 'flex', background: 'rgba(255,255,255,0.05)', borderRadius: '10px', padding: '4px', gap: '4px' }}>
          <button type="button" onClick={() => setIsSignup(false)} style={pillTabStyle(!isSignup)}>
            Login
          </button>
          <button type="button" onClick={() => setIsSignup(true)} style={pillTabStyle(isSignup)}>
            Sign Up
          </button>
        </div>

        {error && <div style={errorStyle}>{error}</div>}

        <form onSubmit={onSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {isSignup && (
          <div>
            <label style={labelStyle}>Username</label>
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              style={inputBaseStyle}
              onFocus={(e) => (e.currentTarget.style.borderColor = 'rgba(212,175,55,0.5)')}
              onBlur={(e) => (e.currentTarget.style.borderColor = 'rgba(255,255,255,0.12)')}
            />
          </div>
        )}
        <div>
          <label style={labelStyle}>Email</label>
          <input
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            style={inputBaseStyle}
            onFocus={(e) => (e.currentTarget.style.borderColor = 'rgba(212,175,55,0.5)')}
            onBlur={(e) => (e.currentTarget.style.borderColor = 'rgba(255,255,255,0.12)')}
          />
        </div>
        <div>
          <label style={labelStyle}>Password</label>
          <div style={{ position: 'relative' }}>
            <input
              type={show ? 'text' : 'password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{ ...inputBaseStyle, paddingRight: '42px' }}
              onFocus={(e) => (e.currentTarget.style.borderColor = 'rgba(212,175,55,0.5)')}
              onBlur={(e) => (e.currentTarget.style.borderColor = 'rgba(255,255,255,0.12)')}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault()
                  onSubmit(e)
                }
              }}
            />
            <button
              type="button"
              onClick={() => setShow((s) => !s)}
              aria-label="Toggle password"
              style={{
                position: 'absolute',
                right: '12px',
                top: '50%',
                transform: 'translateY(-50%)',
                background: 'none',
                border: 'none',
                color: 'rgba(255,255,255,0.4)',
                cursor: 'pointer',
                padding: '0',
                display: 'flex',
                alignItems: 'center',
              }}
            >
              {show ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          style={primaryButtonStyle}
          onMouseEnter={() => setHoveredPrimary(true)}
          onMouseLeave={() => setHoveredPrimary(false)}
        >
          {loading ? <span style={{ display: 'inline-block', animation: 'spin 0.8s linear infinite' }}>◌</span> : isSignup ? 'Sign up' : 'Sign in'}
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: 12, color: 'rgba(255,255,255,0.28)', fontSize: '12px' }}>
          <div style={{ height: 1, background: 'rgba(255,255,255,0.10)', flex: 1 }} />
          <span>or</span>
          <div style={{ height: 1, background: 'rgba(255,255,255,0.10)', flex: 1 }} />
        </div>

        <button
          type="button"
          onClick={onGoogleSignIn}
          style={googleButtonStyle}
          onMouseEnter={() => setHoveredGoogle(true)}
          onMouseLeave={() => setHoveredGoogle(false)}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
            <path fill="#4285F4" d="M21.35 11.1h-9.18v2.97h5.27c-.23 1.43-1.46 4.19-5.27 4.19-3.18 0-5.77-2.63-5.77-5.86s2.59-5.86 5.77-5.86c1.81 0 3.03.77 3.73 1.43l2.54-2.45C17.61 4.99 15.4 4 12.17 4 6.93 4 2.67 8.26 2.67 13.5S6.93 23 12.17 23c5.46 0 9.08-3.84 9.08-9.25 0-.62-.07-1.09-.18-1.65z" />
            <path fill="#34A853" d="M3.96 7.38l3.19 2.34C8.02 7.3 9.94 6.1 12.17 6.1c1.81 0 3.03.77 3.73 1.43l2.54-2.45C17.61 4.99 15.4 4 12.17 4 8.54 4 5.42 6.05 3.96 7.38z" />
            <path fill="#FBBC05" d="M12.17 23c3.18 0 5.84-1.05 7.79-2.85l-3.6-2.96c-.99.68-2.27 1.15-4.19 1.15-3.2 0-5.94-2.16-6.91-5.08l-3.15 2.42C4.49 20.6 8.02 23 12.17 23z" />
            <path fill="#EA4335" d="M12.17 6.1c1.81 0 3.03.77 3.73 1.43l2.54-2.45C17.61 4.99 15.4 4 12.17 4c-3.63 0-6.75 2.05-8.21 3.38l3.19 2.34C8.02 7.3 9.94 6.1 12.17 6.1z" />
          </svg>
          Continue with Google
        </button>

        <button
          type="button"
          style={forgotStyle}
          onClick={() => {
            const emailValue = email.trim()
            if (!emailValue) {
              return
            }
          }}
        >
          Forgot password?
        </button>
        </form>
      </div>
    </div>
  )
}
