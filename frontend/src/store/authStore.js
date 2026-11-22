import { create } from 'zustand'
import { persist } from 'zustand/middleware'

// Giriş bilgisi (tokenlar ve kullanıcı). Tarayıcıda saklanır, sayfa yenilenince giriş kaybolmaz.
export const useAuthStore = create(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      setSession: ({ access_token, refresh_token, user }) =>
        set({ accessToken: access_token, refreshToken: refresh_token, user }),
      setTokens: ({ access_token, refresh_token }) =>
        set({ accessToken: access_token, refreshToken: refresh_token }),
      setUser: (user) => set({ user }),
      logout: () => set({ accessToken: null, refreshToken: null, user: null }),
    }),
    { name: 'kahvecell-auth' },
  ),
)
