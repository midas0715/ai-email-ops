import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "react-router";
import {
  draftDepartmentNotice,
  draftReply,
  getMyTicket,
  listMyDepartments,
  sendTicketEmails,
} from "../api/agent";
import type { DepartmentOption, TicketDetail } from "../api/agent";
import { ErrorText } from "../components/ErrorText";
import { StatusBadge } from "../components/StatusBadge";
import { card, primaryButton, secondaryButton } from "../components/styles";
import { CATEGORY_NAMES } from "../utils/categories";
import { formatDate } from "../utils/format";

const fieldClass =
  "w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500";

function TicketSummary({ ticket }: { ticket: TicketDetail }) {
  const { data, email } = ticket;
  return (
    <section className={`${card} space-y-4`}>
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-xl font-semibold">{email.subject}</h1>
        <StatusBadge status={ticket.status} />
      </div>
      <p className="text-sm text-slate-600">
        From {email.sender_email} · {formatDate(email.received_at)}
      </p>
      <dl className="grid gap-4 text-sm sm:grid-cols-3">
        <div>
          <dt className="text-slate-500">Category</dt>
          <dd className="font-medium">{CATEGORY_NAMES[data.category]}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Priority</dt>
          <dd className="font-medium capitalize">{data.priority}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Customer tone</dt>
          <dd className="font-medium capitalize">{data.sentiment}</dd>
        </div>
      </dl>
      <div className="text-sm">
        <p className="text-slate-500">Summary</p>
        <p>{data.summary}</p>
      </div>
      <div className="text-sm">
        <p className="text-slate-500">What the customer wants</p>
        <p>{data.requested_action}</p>
      </div>
      <details className="text-sm">
        <summary className="cursor-pointer text-indigo-700">Show the original email</summary>
        <div className="mt-2 whitespace-pre-wrap break-words rounded-md bg-slate-50 p-4">
          {email.body}
        </div>
      </details>
    </section>
  );
}

function SentView({ ticket }: { ticket: TicketDetail }) {
  return (
    <div className="space-y-4">
      <section className="rounded-lg border border-green-300 bg-green-50 p-4 text-sm text-green-800">
        Done.{" "}
        {ticket.reply
          ? "The reply was sent to the customer."
          : "No reply is stored for this ticket."}{" "}
        {ticket.escalation
          ? `${ticket.escalation.department} was notified.`
          : "No department was notified."}
      </section>
      {ticket.reply && (
        <section className={`${card} space-y-2`}>
          <h2 className="text-lg font-semibold">Reply to the customer</h2>
          <p className="text-sm text-slate-600">
            To {ticket.reply.to_email} · {formatDate(ticket.reply.sent_at)}
          </p>
          <p className="text-sm text-slate-600">Subject: {ticket.reply.subject}</p>
          <div className="whitespace-pre-wrap break-words rounded-md bg-slate-50 p-4 text-sm">
            {ticket.reply.body}
          </div>
        </section>
      )}
      {ticket.escalation && (
        <section className={`${card} space-y-2`}>
          <h2 className="text-lg font-semibold">Notice to {ticket.escalation.department}</h2>
          <p className="text-sm text-slate-600">
            To {ticket.escalation.to_email} · {formatDate(ticket.escalation.sent_at)}
          </p>
          <p className="text-sm text-slate-600">Subject: {ticket.escalation.subject}</p>
          <div className="whitespace-pre-wrap break-words rounded-md bg-slate-50 p-4 text-sm">
            {ticket.escalation.body}
          </div>
        </section>
      )}
    </div>
  );
}

function SendPanel({
  ticket,
  departments,
}: {
  ticket: TicketDetail;
  departments: DepartmentOption[];
}) {
  const queryClient = useQueryClient();
  const [replyText, setReplyText] = useState("");
  const [sources, setSources] = useState<string[]>([]);
  const [departmentId, setDepartmentId] = useState<number | null>(ticket.suggested_department_id);
  const [noticeText, setNoticeText] = useState("");

  const selected = departments.find((department) => department.id === departmentId) ?? null;

  const reply = useMutation({
    mutationFn: () => draftReply(ticket.email.id),
    onSuccess: (result) => {
      setReplyText(result.reply);
      setSources(result.sources);
    },
  });

  const notice = useMutation({
    mutationFn: (id: number) => draftDepartmentNotice(ticket.id, id),
    onSuccess: (result) => setNoticeText(result.body),
  });

  const send = useMutation({
    mutationFn: () =>
      sendTicketEmails(
        ticket.id,
        selected
          ? { reply_body: replyText, department_id: selected.id, department_body: noticeText }
          : { reply_body: replyText },
      ),
    onSuccess: async () => {
      // The ticket is now completed: refresh it, the lists and the inbox
      await queryClient.invalidateQueries({ queryKey: ["agent", "tickets"] });
      await queryClient.invalidateQueries({ queryKey: ["agent", "emails"] });
    },
  });

  const busy = reply.isPending || notice.isPending || send.isPending;
  const ready = replyText.trim() !== "" && (selected === null || noticeText.trim() !== "");

  return (
    <div className="space-y-6">
      <section className={`${card} space-y-3`}>
        <h2 className="text-lg font-semibold">1. Reply to the customer</h2>
        <label htmlFor="reply" className="block text-sm text-slate-600">
          This is sent to {ticket.email.sender_email}. Write it yourself or let the AI draft it,
          then check every sentence.
        </label>
        <textarea
          id="reply"
          rows={9}
          className={fieldClass}
          value={replyText}
          placeholder="Write a reply, or click Draft with AI..."
          onChange={(event) => setReplyText(event.target.value)}
        />
        <ErrorText error={reply.error} />
        {reply.isPending && (
          <p className="text-sm text-slate-500">
            The AI is reading the email and your company documents...
          </p>
        )}
        {reply.isSuccess && (
          <p className="text-sm text-slate-500">
            {sources.length > 0
              ? `Based on: ${sources.join(", ")}`
              : "No company documents matched, so check the facts yourself."}
          </p>
        )}
        <button
          type="button"
          className={secondaryButton}
          disabled={busy}
          onClick={() => {
            if (replyText.trim() === "" || window.confirm("Replace your text with a new AI draft?")) {
              reply.mutate();
            }
          }}
        >
          {reply.isPending ? "Drafting..." : "Draft with AI"}
        </button>
      </section>

      <section className={`${card} space-y-3`}>
        <h2 className="text-lg font-semibold">2. Notify a department (optional)</h2>
        <label htmlFor="department" className="block text-sm text-slate-600">
          {ticket.suggested_department_id !== null
            ? "The department that handles this category is pre-selected. You can change it."
            : "No department is set up for this category. Pick one, or send the reply only."}
        </label>
        <select
          id="department"
          className={fieldClass}
          value={departmentId === null ? "" : String(departmentId)}
          onChange={(event) => {
            setDepartmentId(event.target.value === "" ? null : Number(event.target.value));
            setNoticeText("");
            notice.reset();
          }}
        >
          <option value="">No department needed</option>
          {departments.map((department) => (
            <option key={department.id} value={department.id}>
              {department.name}
              {department.id === ticket.suggested_department_id ? " (suggested)" : ""}
            </option>
          ))}
        </select>

        {selected && (
          <div className="space-y-3">
            <label htmlFor="notice" className="block text-sm text-slate-600">
              This is sent to {selected.name} ({selected.email}).
            </label>
            <textarea
              id="notice"
              rows={6}
              className={fieldClass}
              value={noticeText}
              placeholder="Write a short note for the department, or click Draft with AI..."
              onChange={(event) => setNoticeText(event.target.value)}
            />
            <ErrorText error={notice.error} />
            {notice.isPending && <p className="text-sm text-slate-500">The AI is writing...</p>}
            <button
              type="button"
              className={secondaryButton}
              disabled={busy}
              onClick={() => {
                if (
                  noticeText.trim() === "" ||
                  window.confirm("Replace your text with a new AI draft?")
                ) {
                  notice.mutate(selected.id);
                }
              }}
            >
              {notice.isPending ? "Drafting..." : "Draft with AI"}
            </button>
          </div>
        )}
      </section>

      <section className="space-y-3">
        <ErrorText error={send.error} />
        <button
          type="button"
          className={primaryButton}
          disabled={busy || !ready}
          onClick={() => {
            const extra = selected ? ` and a notice to ${selected.name}` : "";
            if (
              window.confirm(
                `Send the reply to ${ticket.email.sender_email}${extra}? This cannot be undone.`,
              )
            ) {
              send.mutate();
            }
          }}
        >
          {send.isPending ? "Sending..." : selected ? "Send both emails" : "Send reply"}
        </button>
        {!ready && (
          <p className="text-sm text-slate-500">
            Write the reply{selected ? " and the department note" : ""} to enable sending.
          </p>
        )}
      </section>
    </div>
  );
}

function TicketView({ ticketId }: { ticketId: number }) {
  const ticket = useQuery({
    queryKey: ["agent", "tickets", "detail", ticketId],
    queryFn: () => getMyTicket(ticketId),
  });
  const departments = useQuery({
    queryKey: ["agent", "departments"],
    queryFn: listMyDepartments,
  });

  const sent = ticket.data
    ? ticket.data.status === "completed" || ticket.data.reply !== null
    : false;

  return (
    <div className="space-y-6">
      <Link to="/agent/tickets" className="text-sm text-indigo-700 hover:underline">
        Back to my tickets
      </Link>

      {ticket.isPending && <p className="text-slate-500">Loading...</p>}
      <ErrorText error={ticket.error} />

      {ticket.data && (
        <>
          <TicketSummary ticket={ticket.data} />
          {sent && <SentView ticket={ticket.data} />}
          {!sent && departments.data && (
            <SendPanel ticket={ticket.data} departments={departments.data} />
          )}
          {!sent && departments.isPending && (
            <p className="text-slate-500">Loading departments...</p>
          )}
          {!sent && <ErrorText error={departments.error} />}
        </>
      )}
    </div>
  );
}

export function TicketPage() {
  const params = useParams();
  const ticketId = Number(params.ticketId);

  if (!Number.isInteger(ticketId) || ticketId <= 0) {
    return <p className="text-red-600">This ticket link is not valid.</p>;
  }
  // The key resets all drafts when the agent opens a different ticket
  return <TicketView key={ticketId} ticketId={ticketId} />;
}