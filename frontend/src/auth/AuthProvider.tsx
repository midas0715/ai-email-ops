import { useCallback, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { setUnauthorizedHandler } from "../api/client";
import { AuthContext } from "./context";
import { clearToken, loadSession, saveToken, sessionFromToken } from "./token";
import type { Session } from "./token";

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [session, setSession] = useState<Session | null>(() => loadSession());

  const logout = useCallback(() => {
    clearToken();
    setSession(null);
    queryClient.clear(); // never keep one person's data around for the next login
  }, [queryClient]);

  const login = useCallback(
    (token: string) => {
      const next = sessionFromToken(token);
      if (!next) return false;
      queryClient.clear();
      saveToken(token);
      setSession(next);
      return true;
    },
    [queryClient],
  );

  // Any "401 Unauthorized" from the API means the token is no longer good
  useEffect(() => {
    setUnauthorizedHandler(logout);
    return () => setUnauthorizedHandler(null);
  }, [logout]);

  // Log out by ourselves at the moment the token expires
  useEffect(() => {
    if (!session) return;
    const timer = setTimeout(logout, Math.max(session.expiresAt - Date.now(), 0));
    return () => clearTimeout(timer);
  }, [session, logout]);

  const value = useMemo(
    () => ({ role: session?.role ?? null, login, logout }),
    [session, login, logout],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}