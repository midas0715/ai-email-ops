import type { Category } from "../api/agent";

export const CATEGORY_NAMES: Record<Category, string> = {
  billing: "Billing",
  technical: "Technical",
  account: "Account changes",
  complaint: "Complaint",
  general: "General",
};