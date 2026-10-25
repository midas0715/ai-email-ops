import { Navigate, Outlet } from "react-router";
import { LOGIN_PATH } from "./paths";
import type { Role } from "./token";
import { useAuth } from "./useAuth";

export function RequireRole({ role }: { role: Role }) {
  const auth = useAuth();
  if (auth.role === role) return <Outlet />;
  return <Navigate to={LOGIN_PATH[role]} replace />;
}