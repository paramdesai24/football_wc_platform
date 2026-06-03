import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { isSupabaseConfigured, supabase } from '@/lib/supabase'
import { apiPost } from '@/services/api'

type User = {
  id: string
  email?: string | null
  provider?: string
  username?: string | null
}

type AuthState = {
  user: User | null
  loading: boolean
  initialized: boolean
  error?: string | null
  cooldownUntil?: number | null
  init: () => Promise<void>
  signUp: (email: string, password: string, username?: string) => Promise<void>
  signIn: (email: string, password: string) => Promise<void>
  signInWithGoogle: (redirectTo?: string) => Promise<void>
  signOut: () => Promise<void>
  setUser: (u: User | null) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      loading: true,
      initialized: false,
      error: null,
      cooldownUntil: null,
      init: async () => {
        const currentUser = get().user
        if (currentUser && currentUser.provider === 'custom') {
          set({ loading: false, initialized: true })
          return
        }
        if (!isSupabaseConfigured || !supabase) {
          set({ loading: false, initialized: true, error: null })
          return
        }
        set({ loading: true })
        try {
          const { data, error } = await supabase.auth.getSession()
          if (error) throw error
          const session = data.session
          if (session?.user) {
            const u = { id: session.user.id, email: session.user.email, provider: 'supabase' }
            set({ user: u })
          } else {
            set({ user: null })
          }
        } catch (err: any) {
          set({ error: err?.message ?? String(err) })
        } finally {
          set({ loading: false, initialized: true })
        }
      },
      signUp: async (email, password, username) => {
        set({ loading: true, error: null })
        try {
          const { data, error } = await apiPost<{ id: string; email: string; username: string }>('/api/v1/auth/signup', {
            email,
            password,
            username: username || email.split('@')[0],
          })
          if (error) {
            throw new Error(error)
          }
          if (data) {
            set({ user: { id: data.id, email: data.email, username: data.username, provider: 'custom' } })
          }
        } catch (err: any) {
          set({ error: err?.message ?? String(err) })
        } finally {
          set({ loading: false })
        }
      },
      signIn: async (email, password) => {
        set({ loading: true, error: null })
        try {
          const { data, error } = await apiPost<{ id: string; email: string; username: string }>('/api/v1/auth/login', {
            email,
            password,
          })
          if (error) {
            throw new Error(error)
          }
          if (data) {
            set({ user: { id: data.id, email: data.email, username: data.username, provider: 'custom' } })
          }
        } catch (err: any) {
          set({ error: err?.message ?? String(err) })
        } finally {
          set({ loading: false })
        }
      },
      signInWithGoogle: async (redirectTo) => {
        if (!isSupabaseConfigured || !supabase) {
          set({ error: 'Supabase is not configured yet.' })
          return
        }
        set({ loading: true, error: null })
        try {
          await supabase.auth.signInWithOAuth({ provider: 'google', options: { redirectTo } })
        } catch (err: any) {
          set({ error: err?.message ?? String(err) })
        } finally {
          set({ loading: false })
        }
      },
      signOut: async () => {
        const currentUser = get().user
        set({ loading: true })
        try {
          if (currentUser?.provider === 'supabase' && isSupabaseConfigured && supabase) {
            await supabase.auth.signOut()
          }
        } catch (err: any) {
          set({ error: err?.message ?? String(err) })
        } finally {
          set({ user: null, loading: false })
        }
      },
      setUser: (u) => set({ user: u }),
    }),
    {
      name: 'auth-storage',
      partialize: (s) => ({ user: s.user }),
    },
  ),
)

export default useAuthStore

