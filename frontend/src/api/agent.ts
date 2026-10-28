import { request } from "./client";

// Plain lists instead of enums: the template's TypeScript settings do not allow enums
export const CATEGORIES = ["billing", "technical", "account", "complaint", "general"] as const;
export const PRIORITIES = ["low", "medium", "high", "urgent"] as const;
export const SENTIMENTS = ["positive", "neutral", "negative"] as const;

export type Category = (typeof CATEGORIES)[number];
export type Priority = (typeof PRIORITIES)[number];
export type Sentiment = (typeof SENTIMENTS)[number];
export type TicketStatus = "open" | "pending" | "completed";

export interface TicketDraft {
  summary: string;
  category: Category;
  priority: Priority;
  sentiment: Sentiment;
  requested_action: string;
}

export interface EmailItem {
  id: number;
  sender_email: string;
  subject: string;
  received_at: string;
  has_ticket: boolean;
}

export interface EmailDetail {
  id: number;
  sender_email: string;
  subject: string;
  body: string;
  received_at: string;
  ticket_id: number | null;
}

export interface TicketCreated {
  id: number;
  email_id: number;
  agent_id: number;
  status: TicketStatus;
  data: TicketDraft;
}

export interface TicketItem {
  id: number;
  email_id: number;
  subject: string;
  status: TicketStatus;
  data: TicketDraft;
  created_at: string;
}

export interface ReplyInfo {
  to_email: string;
  subject: string;
  body: string;
  sent_at: string;
}

export interface EscalationInfo {
  department_id: number;
  department: string;
  to_email: string;
  subject: string;
  body: string;
  sent_at: string;
}

export interface TicketDetail {
  id: number;
  status: TicketStatus;
  data: TicketDraft;
  created_at: string;
  updated_at: string;
  email: EmailDetail;
  reply: ReplyInfo | null;
  escalation: EscalationInfo | null;
  suggested_department_id: number | null;
}

export interface DepartmentOption {
  id: number;
  name: string;
  email: string;
  categories: string[];
}

export interface ReplyDraftResult {
  reply: string;
  sources: string[];
}

export interface DepartmentDraftResult {
  department: string;
  to_email: string;
  subject: string;
  body: string;
}

export interface SendPayload {
  reply_body: string;
  department_id?: number;
  department_body?: string;
}

export interface SendResult {
  ticket_id: number;
  status: TicketStatus;
  reply_sent_to: string;
  department_notified: string | null;
}

export function listMyEmails(options: { onlyNew: boolean; limit: number; offset: number }) {
  const params = new URLSearchParams({
    only_new: String(options.onlyNew),
    limit: String(options.limit),
    offset: String(options.offset),
  });
  return request<EmailItem[]>(`/me/emails?${params.toString()}`);
}

export function getMyEmail(emailId: number) {
  return request<EmailDetail>(`/me/emails/${emailId}`);
}

// refresh = true skips the cached draft and asks the AI again
export function startTicket(emailId: number, refresh: boolean) {
  const query = refresh ? "?refresh=true" : "";
  return request<TicketDraft>(`/emails/${emailId}/start-ticket${query}`, { method: "POST" });
}

export function saveTicket(emailId: number, draft: TicketDraft) {
  return request<TicketCreated>(`/emails/${emailId}/ticket`, { method: "POST", json: draft });
}

export function listMyTickets(options: { status?: TicketStatus; limit: number; offset: number }) {
  const params = new URLSearchParams({
    limit: String(options.limit),
    offset: String(options.offset),
  });
  if (options.status) params.set("status", options.status);
  return request<TicketItem[]>(`/me/tickets?${params.toString()}`);
}

export function getMyTicket(ticketId: number) {
  return request<TicketDetail>(`/me/tickets/${ticketId}`);
}

export function listMyDepartments() {
  return request<DepartmentOption[]>("/me/departments");
}

export function draftReply(emailId: number) {
  return request<ReplyDraftResult>(`/emails/${emailId}/draft-reply`, { method: "POST" });
}

export function draftDepartmentNotice(ticketId: number, departmentId: number) {
  return request<DepartmentDraftResult>(`/tickets/${ticketId}/escalation-draft`, {
    method: "POST",
    json: { department_id: departmentId },
  });
}

export function sendTicketEmails(ticketId: number, payload: SendPayload) {
  return request<SendResult>(`/tickets/${ticketId}/send`, { method: "POST", json: payload });
}