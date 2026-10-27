import { request } from "./client";

export interface Agent {
  id: number;
  name: string;
  email: string;
  is_active: boolean;
}

export interface NewAgent {
  name: string;
  email: string;
  password: string;
}

export interface AgentRemoved {
  agent_id: number;
  reassigned_emails: number;
}

export interface Department {
  id: number;
  name: string;
  email: string;
}

export interface NewDepartment {
  name: string;
  email: string;
}

export function listAgents() {
  return request<Agent[]>("/orgs/me/agents");
}

export function createAgent(input: NewAgent) {
  return request<Agent>("/orgs/me/agents", { method: "POST", json: input });
}

export function removeAgent(agentId: number) {
  return request<AgentRemoved>(`/orgs/me/agents/${agentId}`, { method: "DELETE" });
}

export function listDepartments() {
  return request<Department[]>("/orgs/me/departments");
}

export function createDepartment(input: NewDepartment) {
  return request<Department>("/orgs/me/departments", { method: "POST", json: input });
}

export function deleteDepartment(departmentId: number) {
  return request<void>(`/orgs/me/departments/${departmentId}`, { method: "DELETE" });
}