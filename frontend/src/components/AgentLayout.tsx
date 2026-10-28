import { NavLink, Outlet } from "react-router";

const tabs = [
  { to: "/agent", label: "Inbox", end: true },
  { to: "/agent/tickets", label: "My tickets", end: false },
];

export function AgentLayout() {
  return (
    <div>
      <nav className="mb-6 flex gap-1 border-b border-slate-200">
        {tabs.map((tab) => (
          <NavLink
            key={tab.to}
            to={tab.to}
            end={tab.end}
            className={({ isActive }) =>
              `-mb-px border-b-2 px-4 py-2 text-sm font-medium ${
                isActive
                  ? "border-indigo-600 text-indigo-700"
                  : "border-transparent text-slate-600 hover:text-slate-900"
              }`
            }
          >
            {tab.label}
          </NavLink>
        ))}
      </nav>
      <Outlet />
    </div>
  );
}