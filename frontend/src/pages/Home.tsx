import { Link } from "react-router";

const primary =
  "rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700";
const secondary =
  "rounded-md border border-slate-300 px-4 py-2 text-sm font-medium hover:bg-slate-100";

export function Home() {
  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="text-3xl font-bold">AI Email Operations</h1>
      <p className="mt-2 text-slate-600">
        Support emails become tickets and reply drafts through a local AI, and a person always
        reviews them.
      </p>
      <div className="mt-8 grid gap-4 sm:grid-cols-2">
        <section className="rounded-lg border border-slate-200 bg-white p-6">
          <h2 className="text-lg font-semibold">Organization (CEO)</h2>
          <p className="mt-1 text-sm text-slate-600">
            Manage agents, departments, documents and the email API key.
          </p>
          <div className="mt-4 flex gap-3">
            <Link to="/ceo/login" className={primary}>
              Log in
            </Link>
            <Link to="/ceo/register" className={secondary}>
              Register
            </Link>
          </div>
        </section>
        <section className="rounded-lg border border-slate-200 bg-white p-6">
          <h2 className="text-lg font-semibold">Support agent</h2>
          <p className="mt-1 text-sm text-slate-600">
            Work through your inbox, tickets and reply drafts.
          </p>
          <div className="mt-4">
            <Link to="/agent/login" className={primary}>
              Log in
            </Link>
          </div>
        </section>
      </div>
    </div>
  );
}