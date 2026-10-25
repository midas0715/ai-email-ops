import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Link, Navigate } from "react-router";
import { loginAgent, loginOrg } from "../api/auth";
import { HOME_PATH } from "../auth/paths";
import type { Role } from "../auth/token";
import { useAuth } from "../auth/useAuth";
import { Field } from "../components/Field";

const TITLE: Record<Role, string> = { org: "CEO login", agent: "Agent login" };

export function LoginPage({ role }: { role: Role }) {
  const auth = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const mutation = useMutation({
    mutationFn: () =>
      role === "org" ? loginOrg(email, password) : loginAgent(email, password),
    onSuccess: (data) => {
      if (!auth.login(data.access_token)) {
        throw new Error("The server sent a token the app cannot read");
      }
    },
  });

  // Already logged in as this role: go straight to the home page
  if (auth.role === role) return <Navigate to={HOME_PATH[role]} replace />;

  return (
    <div className="mx-auto max-w-sm">
      <h1 className="text-2xl font-semibold">{TITLE[role]}</h1>
      <form
        className="mt-6 space-y-4 rounded-lg border border-slate-200 bg-white p-6"
        onSubmit={(event) => {
          event.preventDefault();
          mutation.mutate();
        }}
      >
        <Field
          label="Email"
          name="email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />
        <Field
          label="Password"
          name="password"
          type="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
        {mutation.isError && (
          <p role="alert" className="text-sm text-red-600">
            {mutation.error.message}
          </p>
        )}
        <button
          type="submit"
          disabled={mutation.isPending}
          className="w-full rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-60"
        >
          {mutation.isPending ? "Logging in..." : "Log in"}
        </button>
      </form>
      {role === "org" && (
        <p className="mt-4 text-sm text-slate-600">
          New organization?{" "}
          <Link to="/ceo/register" className="text-indigo-700 hover:underline">
            Register
          </Link>
        </p>
      )}
    </div>
  );
}