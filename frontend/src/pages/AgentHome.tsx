import { useQuery } from "@tanstack/react-query";
import { getAgentProfile } from "../api/auth";

export function AgentHome() {
  const profile = useQuery({ queryKey: ["agent", "me"], queryFn: getAgentProfile });

  if (profile.isPending) return <p className="text-slate-500">Loading...</p>;
  if (profile.isError) return <p className="text-red-600">{profile.error.message}</p>;

  const agent = profile.data;
  return (
    <div>
      <h1 className="text-2xl font-semibold">Welcome, {agent.name}</h1>
      <p className="mt-1 text-slate-600">
        {agent.organization_name} · {agent.email}
      </p>
      <p className="mt-6 text-sm text-slate-500">Your inbox and tickets will appear here in the next steps.</p>
    </div>
  );
}