import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface IdentityState {
  userId: string
  username: string
  teamName: string
  setUserId: (id: string) => void
  setUsername: (name: string) => void
  setTeamName: (name: string) => void
  clear: () => void
}

export const useIdentityStore = create<IdentityState>()(
  persist(
    (set) => ({
      userId: '',
      username: '',
      teamName: '',
      setUserId: (userId) => set({ userId }),
      setUsername: (username) => set({ username }),
      setTeamName: (teamName) => set({ teamName }),
      clear: () => set({ userId: '', username: '', teamName: '' }),
    }),
    { name: 'fc-analytics-identity' },
  ),
)
