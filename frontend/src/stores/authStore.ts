import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { AuthTokens, CurrentUser } from '@/types/api'

interface AuthState {
  user: CurrentUser | null
  isAuthenticated: boolean
  setSession: (tokens: AuthTokens) => void
  setUser: (user: CurrentUser | null) => void
  clear: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: !!localStorage.getItem('access_token'),

      setSession: (tokens: AuthTokens) => {
        localStorage.setItem('access_token', tokens.access_token)
        localStorage.setItem('refresh_token', tokens.refresh_token)
        set({
          isAuthenticated: true,
          user: {
            id: tokens.user_id,
            email: tokens.email,
            full_name: tokens.full_name,
            is_active: true,
            is_superuser: false,
          },
        })
      },

      setUser: (user) => set({ user }),

      clear: () => {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        set({ user: null, isAuthenticated: false })
      },
    }),
    {
      name: 'auth-store',
      partialize: (state) => ({ user: state.user }),
    },
  ),
)
