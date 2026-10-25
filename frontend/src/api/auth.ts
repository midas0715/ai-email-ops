import { request } from "./client";

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface OrgProfile {
  id: number;
  name: string;
  email: string | null;
  api_key_hint: string | null;
}

export interface AgentProfile {
  id: number;
  name: string;
  email: string;
  organization_id: number;
  organization_name: string;
}

export function loginAgent(email: string, password: string) {
  return request<TokenResponse>("/auth/login", {
    method: "POST",
    form: { username: email, password },
    auth: false,
  });
}

export function loginOrg(email: string, password: string) {
  return request<TokenResponse>("/auth/org-login", {
    method: "POST",
    form: { username: email, password },
    auth: false,
  });
}

export function registerOrg(input: { name: string; email: string; password: string }) {
  return request<OrgProfile>("/orgs/register", { method: "POST", json: input, auth: false });
}

export function getOrgProfile() {
  return request<OrgProfile>("/orgs/me");
}

export function getAgentProfile() {
  return request<AgentProfile>("/me");
}