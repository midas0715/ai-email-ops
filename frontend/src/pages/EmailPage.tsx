import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router";
import { getMyEmail, saveTicket, startTicket } from "../api/agent";
import type { TicketDraft } from "../api/agent";
import { ErrorText } from "../components/ErrorText";
import { TicketDraftForm } from "../components/TicketDraftForm";
import { card, primaryButton } from "../components/styles";
import { formatDate } from "../utils/format";

function EmailView({ emailId }: { emailId: number }) {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [draft, setDraft] = useState<TicketDraft | null>(null);
  const [draftVersion, setDraftVersion] = useState(0);

  const email = useQuery({
    queryKey: ["agent", "emails", "detail", emailId],
    queryFn: () => getMyEmail(emailId),
  });

  const start = useMutation({
    mutationFn: (refresh: boolean) => startTicket(emailId, refresh),
    onSuccess: (data) => {
      setDraft(data);
      setDraftVersion((version) => version + 1); // a new key makes the form start fresh
    },
  });

  const save = useMutation({
    mutationFn: (ticket: TicketDraft) => saveTicket(emailId, ticket),
    onSuccess: async (created) => {
      setDraft(null);
      // Refreshes the inbox lists and this email, so the status badge updates
      await queryClient.invalidateQueries({ queryKey: ["agent", "emails"] });
      navigate(`/agent/tickets/${created.id}`);
    },
  });

  return (
    <div className="space-y-6">
      <Link to="/agent" className="text-sm text-indigo-700 hover:underline">
        Back to inbox
      </Link>

      {email.isPending && <p className="text-slate-500">Loading...</p>}
      <ErrorText error={email.error} />

      {email.data && (
        <>
          <section className={`${card} space-y-3`}>
            <h1 className="text-xl font-semibold">{email.data.subject}</h1>
            <p className="text-sm text-slate-600">
              From {email.data.sender_email} · {formatDate(email.data.received_at)}
            </p>
            {/* Shown as plain text on purpose: emails come from outside and are not trusted */}
            <div className="whitespace-pre-wrap break-words rounded-md bg-slate-50 p-4 text-sm">
              {email.data.body}
            </div>
          </section>

          {email.data.ticket_id !== null ? (
            <section className="rounded-lg border border-green-300 bg-green-50 p-4 text-sm text-green-800">
              A ticket already exists for this email.{" "}
              <Link
                to={`/agent/tickets/${email.data.ticket_id}`}
                className="font-medium underline"
              >
                Open ticket #{email.data.ticket_id}
              </Link>
            </section>
          ) : draft ? (
            <TicketDraftForm
              key={draftVersion}
              initial={draft}
              saving={save.isPending}
              regenerating={start.isPending}
              error={save.error ?? start.error}
              onSave={(ticket) => save.mutate(ticket)}
              onRegenerate={() => start.mutate(true)}
            />
          ) : (
            <section className={`${card} space-y-3`}>
              <h2 className="text-lg font-semibold">Start a ticket</h2>
              <p className="text-sm text-slate-600">
                The AI reads this email and fills in a ticket form for you to review.
              </p>
              <ErrorText error={start.error} />
              {start.isPending && (
                <p className="text-sm text-slate-500">
                  The AI is reading the email. The first request can take up to a minute while the
                  model loads.
                </p>
              )}
              <button
                className={primaryButton}
                disabled={start.isPending}
                onClick={() => start.mutate(false)}
              >
                {start.isPending ? "Working..." : "Start a ticket"}
              </button>
            </section>
          )}
        </>
      )}
    </div>
  );
}

export function EmailPage() {
  const params = useParams();
  const emailId = Number(params.emailId);

  if (!Number.isInteger(emailId) || emailId <= 0) {
    return <p className="text-red-600">This email link is not valid.</p>;
  }
  // The key makes React throw away all state when the agent opens a different email,
  // so a draft for one email can never show up on another
  return <EmailView key={emailId} emailId={emailId} />;
}