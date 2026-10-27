import { useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { Link } from "react-router";
import { listMyEmails } from "../api/agent";
import { getAgentProfile } from "../api/auth";
import { ErrorText } from "../components/ErrorText";
import { card, secondaryButton } from "../components/styles";
import { formatDate } from "../utils/format";

const PAGE_SIZE = 20;

export function InboxPage() {
  const [onlyNew, setOnlyNew] = useState(true);
  const [page, setPage] = useState(0);

  const profile = useQuery({ queryKey: ["agent", "me"], queryFn: getAgentProfile });
  const emails = useQuery({
    queryKey: ["agent", "emails", "list", { onlyNew, page }],
    // Ask for one extra row: if it comes back, there is a next page
    queryFn: () => listMyEmails({ onlyNew, limit: PAGE_SIZE + 1, offset: page * PAGE_SIZE }),
    placeholderData: keepPreviousData, // keep showing the old page while the next one loads
  });

  const rows = emails.data?.slice(0, PAGE_SIZE) ?? [];
  const hasNext = (emails.data?.length ?? 0) > PAGE_SIZE;

  return (
    <div className="space-y-6">
      <section>
        <h1 className="text-2xl font-semibold">Inbox</h1>
        {profile.data && (
          <p className="mt-1 text-sm text-slate-600">
            Welcome, {profile.data.name} ({profile.data.organization_name})
          </p>
        )}
      </section>

      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={onlyNew}
          onChange={(event) => {
            setOnlyNew(event.target.checked);
            setPage(0);
          }}
        />
        Show only new emails (no ticket yet)
      </label>

      {emails.isPending && <p className="text-slate-500">Loading...</p>}
      <ErrorText error={emails.error} />
      {emails.data && rows.length === 0 && (
        <p className="text-slate-500">
          {onlyNew ? "No new emails right now." : "Your inbox is empty."}
        </p>
      )}

      {rows.length > 0 && (
        <div className={`${card} overflow-x-auto p-0`}>
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-200 text-slate-500">
              <tr>
                <th className="px-4 py-3 font-medium">Subject</th>
                <th className="px-4 py-3 font-medium">From</th>
                <th className="px-4 py-3 font-medium">Received</th>
                <th className="px-4 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((email) => (
                <tr key={email.id} className="border-b border-slate-100 last:border-0">
                  <td className="px-4 py-3">
                    <Link
                      to={`/agent/emails/${email.id}`}
                      className="font-medium text-indigo-700 hover:underline"
                    >
                      {email.subject}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-slate-600">{email.sender_email}</td>
                  <td className="px-4 py-3 text-slate-600">{formatDate(email.received_at)}</td>
                  <td className="px-4 py-3">
                    {email.has_ticket ? (
                      <span className="rounded-full bg-green-50 px-2 py-0.5 text-green-700">
                        Ticket created
                      </span>
                    ) : (
                      <span className="rounded-full bg-amber-50 px-2 py-0.5 text-amber-700">
                        New
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {(page > 0 || hasNext) && (
        <div className="flex items-center justify-between">
          <button
            className={secondaryButton}
            disabled={page === 0}
            onClick={() => setPage(page - 1)}
          >
            Previous
          </button>
          <span className="text-sm text-slate-500">Page {page + 1}</span>
          <button className={secondaryButton} disabled={!hasNext} onClick={() => setPage(page + 1)}>
            Next
          </button>
        </div>
      )}
    </div>
  );
}