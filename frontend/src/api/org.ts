import { request } from "./client";
import type { Category } from "./agent";

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
  categories: Category[];
}

export interface NewDepartment {
  name: string;
  email: string;
  categories: Category[];
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

export function setDepartmentCategories(departmentId: number, categories: Category[]) {
  return request<Department>(`/orgs/me/departments/${departmentId}/categories`, {
    method: "PUT",
    json: { categories },
  });
}

export function deleteDepartment(departmentId: number) {
  return request<void>(`/orgs/me/departments/${departmentId}`, { method: "DELETE" });
}

export interface ApiKeyCreated {
  api_key: string;
  hint: string;
  note: string;
}

export interface KnowledgeDoc {
  id: number;
  filename: string;
  size_bytes: number;
  chunk_count: number;
  created_at: string;
}

export function createApiKey() {
  return request<ApiKeyCreated>("/orgs/me/api-key", { method: "POST" });
}

export function revokeApiKey() {
  return request<void>("/orgs/me/api-key", { method: "DELETE" });
}

export function listDocuments() {
  return request<KnowledgeDoc[]>("/orgs/me/knowledge");
}

export function uploadDocument(file: File) {
  const formData = new FormData();
  formData.append("file", file); // the API expects the field to be called "file"
  return request<KnowledgeDoc>("/orgs/me/knowledge", { method: "POST", formData });
}

export function deleteDocument(documentId: number) {
  return request<void>(`/orgs/me/knowledge/${documentId}`, { method: "DELETE" });
}