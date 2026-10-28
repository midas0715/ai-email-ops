import { useState } from "react";
import { CATEGORIES, PRIORITIES, SENTIMENTS } from "../api/agent";
import type { Category, Priority, Sentiment, TicketDraft } from "../api/agent";
import { ErrorText } from "./ErrorText";
import { card, primaryButton, secondaryButton } from "./styles";

interface TicketDraftFormProps {
  initial: TicketDraft;
  saving: boolean;
  regenerating: boolean;
  error: Error | null;
  onSave: (draft: TicketDraft) => void;
  onRegenerate: () => void;
}

const CATEGORY_LABELS: Record<Category, string> = {
  billing: "Billing / finance (payments, refunds, invoices)",
  technical: "Technical (bugs, errors, login problems)",
  account: "Account changes (profile, plan, close account)",
  complaint: "Complaint",
  general: "General question",
};

const inputClass =
  "w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500";
const labelClass = "mb-1 block text-sm font-medium text-slate-700";

export function TicketDraftForm({
  initial,
  saving,
  regenerating,
  error,
  onSave,
  onRegenerate,
}: TicketDraftFormProps) {
  const [draft, setDraft] = useState<TicketDraft>(initial);
  const busy = saving || regenerating;

  return (
    <form
      className={`${card} space-y-4`}
      onSubmit={(event) => {
        event.preventDefault();
        onSave(draft);
      }}
    >
      <div>
        <h2 className="text-lg font-semibold">AI ticket draft</h2>
        <p className="mt-1 text-sm text-slate-600">
          The AI wrote this from the email. Check every field and fix anything that is wrong.
          Nothing is stored until you click Save.
        </p>
      </div>

      <div>
        <label htmlFor="summary" className={labelClass}>
          Summary
        </label>
        <textarea
          id="summary"
          required
          rows={3}
          className={inputClass}
          value={draft.summary}
          onChange={(event) => setDraft({ ...draft, summary: event.target.value })}
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div>
          <label htmlFor="category" className={labelClass}>
            Category
          </label>
          <select
            id="category"
            className={inputClass}
            value={draft.category}
            onChange={(event) => setDraft({ ...draft, category: event.target.value as Category })}
          >
            {CATEGORIES.map((value) => (
              <option key={value} value={value}>
                {CATEGORY_LABELS[value]}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="priority" className={labelClass}>
            Priority
          </label>
          <select
            id="priority"
            className={`${inputClass} capitalize`}
            value={draft.priority}
            onChange={(event) => setDraft({ ...draft, priority: event.target.value as Priority })}
          >
            {PRIORITIES.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="sentiment" className={labelClass}>
            Customer tone
          </label>
          <select
            id="sentiment"
            className={`${inputClass} capitalize`}
            value={draft.sentiment}
            onChange={(event) =>
              setDraft({ ...draft, sentiment: event.target.value as Sentiment })
            }
          >
            {SENTIMENTS.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <label htmlFor="requested_action" className={labelClass}>
          What the customer wants
        </label>
        <textarea
          id="requested_action"
          required
          rows={2}
          className={inputClass}
          value={draft.requested_action}
          onChange={(event) => setDraft({ ...draft, requested_action: event.target.value })}
        />
      </div>

      <ErrorText error={error} />
      <div className="flex flex-wrap gap-3">
        <button type="submit" disabled={busy} className={primaryButton}>
          {saving ? "Saving..." : "Save ticket"}
        </button>
        <button
          type="button"
          disabled={busy}
          className={secondaryButton}
          onClick={() => {
            if (window.confirm("Replace your edits with a new AI draft?")) onRegenerate();
          }}
        >
          {regenerating ? "Asking the AI..." : "Regenerate draft"}
        </button>
      </div>
    </form>
  );
}