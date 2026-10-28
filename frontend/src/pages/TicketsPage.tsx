import { useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { Link } from "react-router";
import { listMyTickets } from "../api/agent";
import type { TicketStatus } from "../api/agent";
import { ErrorText } from "../components/ErrorText";
import { StatusBadge } from "../components/StatusBadge";
import { card, secondaryButton } from "../components/styles";
import { CATEGORY_NAMES } from "../utils/categories";
import { formatDate } from "../utils/format";

const PAGE_SIZE = 20;
type Filter = "all" | TicketStatus;

export function TicketsPage() {
  const [filter, setFilter] = useState<Filter>("all");
  const [page, setPage] = useState(0);

  const tickets = useQuery({
    queryKey: ["agent", "tickets", "list", { filter, page }],
    // Ask for one extra row: if it comes back, there is a next page
    queryFn: () =>
      listMyTickets({
        status: filter === "all" ? undefined : filter,
        limit: PAGE_SIZE + 1,
        offset: page * PAGE_SIZE,
      }),
    placeholderData: keepPreviousData,
  });

  const rows = tickets.data?.slice(0, PAGE_SIZE) ?? [];
  const hasNext = (tickets.data?.length ?? 0) > PAGE_SIZE;

  return (
    <div className="space-y-6">
      <section className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">My tickets</h1>
          <p className="mt-1 text-sm text-slate-600">Every ticket you raised, newest first.</p>
        </div>
        <label className="text-sm">
          <span className="mr-2 text-slate-600">Show</span>
          <select
            className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
            value={filter}
            onChange={(event) => {
              setFilter(event.target.value as Filter);
              setPage(0);
            }}
          >
            <option value="all">All tickets</option>
            <option value="open">Open (not sent yet)</option>
            <option value="completed">Completed</option>
          </select>
        </label>
      </section>

      {tickets.isPending && <p className="text-slate-500">Loading...</p>}
      <ErrorText error={tickets.error} />
      {tickets.data && rows.length === 0 && <p className="text-slate-500">No tickets here yet.</p>}

      {rows.length > 0 && (
        <div className={`${card} overflow-x-auto p-0`}>
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-200 text-slate-500">
              <tr>
                <th className="px-4 py-3 font-medium">Subject</th>
                <th className="px-4 py-3 font-medium">Category</th>
                <th className="px-4 py-3 font-medium">Priority</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Created</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((ticket) => (
                <tr key={ticket.id} className="border-b border-slate-100 last:border-0">
                  <td className="px-4 py-3">
                    <Link
                      to={`/agent/tickets/${ticket.id}`}
                      className="font-medium text-indigo-700 hover:underline"
                    >
                      {ticket.subject}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    {CATEGORY_NAMES[ticket.data.category]}
                  </td>
                  <td className="px-4 py-3 capitalize text-slate-600">{ticket.data.priority}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={ticket.status} />
                  </td>
                  <td className="px-4 py-3 text-slate-600">{formatDate(ticket.created_at)}</td>
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