// Global auth state: current user + login/register/logout. Any component can call
// useAuth() to gate content or show the account status.
import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import * as authApi from "./auth";
import type { User } from "./types";

interface AuthValue {
  user: User | null;
  loading: boolean; // true while restoring a saved session on first load
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name?: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // On first load, restore a saved token by fetching the current user.
  useEffect(() => {
    if (!authApi.tokenStore.get()) {
      setLoading(false);
      return;
    }
    authApi
      .fetchMe()
      .then(setUser)
      .catch(() => authApi.tokenStore.clear())
      .finally(() => setLoading(false));
  }, []);

  async function afterToken(token: string) {
    authApi.tokenStore.set(token);
    setUser(await authApi.fetchMe());
  }

  const value = useMemo<AuthValue>(
    () => ({
      user,
      loading,
      login: async (email, password) => afterToken(await authApi.login(email, password)),
      register: async (email, password, name) =>
        afterToken(await authApi.register(email, password, name)),
      logout: () => {
        authApi.tokenStore.clear();
        setUser(null);
      },
    }),
    [user, loading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
