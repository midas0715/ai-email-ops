import { Link, Outlet, useNavigate } from "react-router";
import type { Role } from "../auth/token";
import { useAuth } from "../auth/useAuth";

const ROLE_LABEL: Record<Role, string> = { org: "CEO", agent: "Agent" };

export function Layout() {
  const auth = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
          <Link to="/" className="font-semibold text-indigo-700">
            AI Email Ops
          </Link>
          {auth.role && (
            <div className="flex items-center gap-3 text-sm">
              <span className="rounded-full bg-indigo-50 px-2 py-0.5 text-indigo-700">
                {ROLE_LABEL[auth.role]}
              </span>
              <button
                onClick={() => {
                  auth.logout();
                  navigate("/");
                }}
                className="text-slate-600 hover:text-slate-900"
              >
                Log out
              </button>
            </div>
          )}
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
}