import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createAgent, listAgents, removeAgent } from "../api/org";
import { ErrorText } from "../components/ErrorText";
import { Field } from "../components/Field";
import { card, dangerButton, primaryButton } from "../components/styles";

const AGENTS_KEY = ["org", "agents"];

function AddAgentForm() {
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const mutation = useMutation({
    mutationFn: () => createAgent({ name, email, password }),
    onSuccess: async () => {
      setName("");
      setEmail("");
      setPassword("");
      // Tell TanStack Query the cached list is out of date, so the table reloads
      await queryClient.invalidateQueries({ queryKey: AGENTS_KEY });
    },
  });

  return (
    <form
      className={`${card} space-y-4`}
      onSubmit={(event) => {
        event.preventDefault();
        mutation.mutate();
      }}
    >
      <h2 className="text-lg font-semibold">Add an agent</h2>
      <div className="grid gap-4 sm:grid-cols-3">
        <Field
          label="Name"
          name="name"
          required
          minLength={2}
          maxLength={200}
          value={name}
          onChange={(event) => setName(event.target.value)}
        />
        <Field
          label="Email"
          name="email"
          type="email"
          autoComplete="off"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />
        <Field
          label="Password (8+ characters)"
          name="password"
          type="password"
          autoComplete="new-password"
          required
          minLength={8}
          maxLength={72}
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
      </div>
      <ErrorText error={mutation.error} />
      <button type="submit" disabled={mutation.isPending} className={primaryButton}>
        {mutation.isPending ? "Adding..." : "Add agent"}
      </button>
    </form>
  );
}

export function AgentsPage() {
  const queryClient = useQueryClient();
  const agents = useQuery({ queryKey: AGENTS_KEY, queryFn: listAgents });

  const remove = useMutation({
    mutationFn: removeAgent,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: AGENTS_KEY }),
  });

  return (
    <div className="space-y-8">
      <section>
        <h1 className="text-2xl font-semibold">Support agents</h1>
        <p className="mt-1 text-sm text-slate-600">
          Each agent logs in with their own email and password. New emails are assigned randomly
          among the active agents.
        </p>
      </section>

      <AddAgentForm />

      <section className="space-y-3">
        {agents.isPending && <p className="text-slate-500">Loading...</p>}
        <ErrorText error={agents.error} />
        {agents.data && agents.data.length === 0 && (
          <p className="text-slate-500">No agents yet. Add your first one above.</p>
        )}
        {agents.data && agents.data.length > 0 && (
          <div className={`${card} overflow-x-auto p-0`}>
            <table className="w-full text-left text-sm">
              <thead className="border-b border-slate-200 text-slate-500">
                <tr>
                  <th className="px-4 py-3 font-medium">Name</th>
                  <th className="px-4 py-3 font-medium">Email</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody>
                {agents.data.map((agent) => (
                  <tr key={agent.id} className="border-b border-slate-100 last:border-0">
                    <td className="px-4 py-3">{agent.name}</td>
                    <td className="px-4 py-3 text-slate-600">{agent.email}</td>
                    <td className="px-4 py-3">
                      {agent.is_active ? (
                        <span className="rounded-full bg-green-50 px-2 py-0.5 text-green-700">
                          Active
                        </span>
                      ) : (
                        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-slate-500">
                          Removed
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {agent.is_active && (
                        <button
                          className={dangerButton}
                          disabled={remove.isPending}
                          onClick={() => {
                            if (
                              window.confirm(
                                `Remove ${agent.name}? They will no longer be able to log in.`,
                              )
                            ) {
                              remove.mutate(agent.id);
                            }
                          }}
                        >
                          Remove
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <ErrorText error={remove.error} />
        {remove.isSuccess && (
          <p className="text-sm text-green-700">
            Agent removed. {remove.data.reassigned_emails} waiting email(s) were handed to other
            agents.
          </p>
        )}
      </section>
    </div>
  );
}