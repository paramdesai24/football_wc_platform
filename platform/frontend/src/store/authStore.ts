import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { isSupabaseConfigured, supabase } from '@/lib/supabase'

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

export const useAuthStore = create<AuthState>(
  persist(
    (set, get) => ({
      user: null,
      loading: true,
      initialized: false,
      error: null,
      cooldownUntil: null,
      init: async () => {
        if (!isSupabaseConfigured || !supabase) {
          set({ loading: false, initialized: true, error: 'Supabase is not configured yet.' })
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
          }
        } catch (err: any) {
          set({ error: err?.message ?? String(err) })
        } finally {
          set({ loading: false, initialized: true })
        }
      },
      signUp: async (email, password, username) => {
        if (!isSupabaseConfigured || !supabase) {
          set({ error: 'Supabase is not configured yet.' })
          return
        }
        set({ loading: true, error: null })
        try {
          const { data, error } = await supabase.auth.signUp({ email, password }, { data: { username } })
          if (error) {
            if (/rate/i.test(error.message)) {
              set({ cooldownUntil: Date.now() + 60_000 })
            }
            throw error
          }
          // For email signups, Supabase may require confirmation. We'll not assume immediate session.
          if (data?.user) {
            set({ user: { id: data.user.id, email: data.user.email, username } })
          }
        } catch (err: any) {
          set({ error: err?.message ?? String(err) })
        } finally {
          set({ loading: false })
        }
      },
      signIn: async (email, password) => {
        if (!isSupabaseConfigured || !supabase) {
          set({ error: 'Supabase is not configured yet.' })
          return
        }
        set({ loading: true, error: null })
        try {
          const { data, error } = await supabase.auth.signInWithPassword({ email, password })
          if (error) {
            if (/rate/i.test(error.message)) set({ cooldownUntil: Date.now() + 60_000 })
            throw error
          }
          if (data?.user) {
            set({ user: { id: data.user.id, email: data.user.email } })
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
        if (!isSupabaseConfigured || !supabase) {
          set({ user: null, error: 'Supabase is not configured yet.' })
          return
        }
        set({ loading: true })
        try {
          await supabase.auth.signOut()
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
      getStorage: () => localStorage,
      partialize: (s) => ({ user: s.user }),
    },
  ),
)

export default useAuthStore
