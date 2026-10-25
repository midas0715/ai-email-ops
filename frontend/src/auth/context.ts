import { createContext } from "react";
import type { Role } from "./token";

export interface AuthState {
  role: Role | null;
  login: (token: string) => boolean;
  logout: () => void;
}

export const AuthContext = createContext<AuthState | null>(null);