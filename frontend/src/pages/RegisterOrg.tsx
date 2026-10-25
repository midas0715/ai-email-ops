import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Link, Navigate } from "react-router";
import { loginOrg, registerOrg } from "../api/auth";
import { HOME_PATH } from "../auth/paths";
import { useAuth } from "../auth/useAuth";
import { Field } from "../components/Field";

export function RegisterOrg() {
  const auth = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const mutation = useMutation({
    mutationFn: async () => {
      await registerOrg({ name, email, password });
      return loginOrg(email, password);
    },
    onSuccess: (data) => {
      if (!auth.login(data.access_token)) {
        throw new Error("The server sent a token the app cannot read");
      }
    },
  });

  if (auth.role === "org") return <Navigate to={HOME_PATH.org} replace />;

  return (
    <div className="mx-auto max-w-sm">
      <h1 className="text-2xl font-semibold">Register your organization</h1>
      <form
        className="mt-6 space-y-4 rounded-lg border border-slate-200 bg-white p-6"
        onSubmit={(event) => {
          event.preventDefault();
          mutation.mutate();
        }}
      >
        <Field
          label="Organization name"
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
          autoComplete="email"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />
        <Field
          label="Password (at least 8 characters)"
          name="password"
          type="password"
          autoComplete="new-password"
          required
          minLength={8}
          maxLength={72}
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
          {mutation.isPending ? "Creating..." : "Create organization"}
        </button>
      </form>
      <p className="mt-4 text-sm text-slate-600">
        Already registered?{" "}
        <Link to="/ceo/login" className="text-indigo-700 hover:underline">
          Log in
        </Link>
      </p>
    </div>
  );
}