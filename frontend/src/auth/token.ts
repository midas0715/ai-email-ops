export type Role = "agent" | "org";

const STORAGE_KEY = "ai-email-ops.token";

export interface Session {
  token: string;
  role: Role;
  expiresAt: number; // milliseconds since 1970, like Date.now()
}

// A token has three parts separated by dots. The middle part is JSON that anyone can read.
function decodePayload(token: string): { role?: unknown; exp?: unknown } | null {
  try {
    const middle = token.split(".")[1];
    const base64 = middle.replace(/-/g, "+").replace(/_/g, "/");
    const padded = base64.padEnd(Math.ceil(base64.length / 4) * 4, "=");
    return JSON.parse(atob(padded));
  } catch {
    return null;
  }
}

/** Only used to decide what to show. The server checks every request again. */
export function sessionFromToken(token: string): Session | null {
  const payload = decodePayload(token);
  if (!payload || typeof payload.exp !== "number") return null;

  const role = payload.role;
  if (role !== "agent" && role !== "org") return null;

  const expiresAt = payload.exp * 1000;
  if (expiresAt <= Date.now()) return null;
  return { token, role, expiresAt };
}

export function loadSession(): Session | null {
  const token = localStorage.getItem(STORAGE_KEY);
  return token ? sessionFromToken(token) : null;
}

export function saveToken(token: string): void {
  localStorage.setItem(STORAGE_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(STORAGE_KEY);
}