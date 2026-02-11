import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  actor: any | null;
  isAuthenticated: boolean;
  login: (accessToken: string, refreshToken: string, actor: any) => void;
  logout: () => void;
  setActor: (actor: any) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      actor: null,
      isAuthenticated: false,
      login: (accessToken, refreshToken, actor) =>
        set({ accessToken, refreshToken, actor, isAuthenticated: true }),
      logout: () =>
        set({
          accessToken: null,
          refreshToken: null,
          actor: null,
          isAuthenticated: false,
        }),
      setActor: (actor) => set({ actor }),
    }),
    {
      name: "madavola-auth",
    }
  )
);
