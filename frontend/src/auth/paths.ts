import type { Role } from "./token";

export const HOME_PATH: Record<Role, string> = { org: "/ceo", agent: "/agent" };
export const LOGIN_PATH: Record<Role, string> = { org: "/ceo/login", agent: "/agent/login" };