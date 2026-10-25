import { useQuery } from "@tanstack/react-query";
import { getOrgProfile } from "../api/auth";

export function CeoHome() {
  const profile = useQuery({ queryKey: ["org", "me"], queryFn: getOrgProfile });

  if (profile.isPending) return <p className="text-slate-500">Loading...</p>;
  if (profile.isError) return <p className="text-red-600">{profile.error.message}</p>;

  const org = profile.data;
  return (
    <div>
      <h1 className="text-2xl font-semibold">{org.name}</h1>
      <p className="mt-1 text-slate-600">{org.email}</p>
      <p className="mt-4 text-sm text-slate-500">
        API key: {org.api_key_hint ? `ends in ${org.api_key_hint}` : "not created yet"}
      </p>
      <p className="mt-6 text-sm text-slate-500">
        Agents, departments and documents will appear here in the next steps.
      </p>
    </div>
  );
}