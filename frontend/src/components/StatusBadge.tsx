import type { TicketStatus } from "../api/agent";

const styles: Record<TicketStatus, string> = {
  open: "bg-amber-50 text-amber-700",
  pending: "bg-blue-50 text-blue-700",
  completed: "bg-green-50 text-green-700",
};

const labels: Record<TicketStatus, string> = {
  open: "Open",
  pending: "Pending",
  completed: "Completed",
};

export function StatusBadge({ status }: { status: TicketStatus }) {
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${styles[status]}`}>
      {labels[status]}
    </span>
  );
}