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