import {
  Bot,
  FileText,
  Gauge,
  LogOut,
  Mail,
  MessageSquare,
  Network,
  Settings,
  Sparkles,
  Users,
  Workflow,
  X,
} from "lucide-react";

import { useAuth } from "../context/AuthContext";

const items = [
  ["dashboard", "Dashboard", Gauge],
  ["chat", "AI Chat", MessageSquare],
  ["documents", "Documents", FileText],
  ["email", "Email Assistant", Mail],
  ["meetings", "Meeting Assistant", Users],
  ["workflows", "Workflows", Workflow],
  ["agent", "AI Agent", Bot],
  ["settings", "Settings", Settings],
];

export default function Sidebar({
  page,
  setPage,
  open,
  setOpen,
}) {
  const { user, logout } = useAuth();

  return (
    <>
      {open && (
        <button
          className="fixed inset-0 z-30 bg-black/65 backdrop-blur-sm lg:hidden"
          onClick={() => setOpen(false)}
          aria-label="Close navigation"
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-40 w-[292px] border-r border-white/[0.07] bg-[#090a0f]/90 p-4 backdrop-blur-2xl transition-transform duration-300 lg:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <button
          className="absolute right-4 top-4 text-zinc-500 lg:hidden"
          onClick={() => setOpen(false)}
        >
          <X size={19} />
        </button>

        <button
          className="mb-8 flex w-full items-center gap-3 rounded-2xl px-2 py-3 text-left"
          onClick={() => setPage("dashboard")}
        >
          <div className="relative grid h-11 w-11 place-items-center rounded-2xl bg-gradient-to-br from-indigo-500 via-violet-500 to-fuchsia-500 shadow-lg shadow-violet-950/50">
            <Network size={21} />
            <span className="absolute -right-1 -top-1 h-3 w-3 rounded-full border-2 border-[#090a0f] bg-emerald-400" />
          </div>
          <div>
            <p className="font-bold tracking-tight">AI Workplace</p>
            <p className="text-xs text-zinc-500">Automation Hub</p>
          </div>
        </button>

        <div className="mb-3 px-3 text-[10px] font-semibold uppercase tracking-[0.2em] text-zinc-600">
          Workspace
        </div>

        <nav className="space-y-1.5">
          {items.map(([id, label, Icon]) => {
            const active = page === id;

            return (
              <button
                key={id}
                onClick={() => {
                  setPage(id);
                  setOpen(false);
                }}
                className={`group relative flex w-full items-center gap-3 overflow-hidden rounded-2xl px-3 py-3 text-sm transition duration-200 ${
                  active
                    ? "bg-gradient-to-r from-indigo-500/18 to-fuchsia-500/8 text-white shadow-inner shadow-white/[0.03]"
                    : "text-zinc-500 hover:bg-white/[0.045] hover:text-zinc-200"
                }`}
              >
                {active && (
                  <span className="absolute inset-y-3 left-0 w-[3px] rounded-full bg-gradient-to-b from-indigo-400 to-fuchsia-400" />
                )}

                <Icon
                  size={18}
                  className={
                    active
                      ? "text-indigo-300"
                      : "transition group-hover:text-zinc-300"
                  }
                />

                <span>{label}</span>

                {id === "agent" && (
                  <Sparkles
                    size={13}
                    className="ml-auto text-fuchsia-400/70"
                  />
                )}
              </button>
            );
          })}
        </nav>

        <div className="absolute bottom-5 left-4 right-4 rounded-2xl border border-white/[0.07] bg-white/[0.035] p-3">
          <div className="flex items-center gap-3">
            <div className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-indigo-500/15 text-sm font-bold text-indigo-200">
              {user?.name?.trim()?.[0]?.toUpperCase() || "U"}
            </div>

            <div className="min-w-0 flex-1">
              <p className="truncate text-xs font-semibold text-zinc-300">
                {user?.name}
              </p>
              <p className="truncate text-[10px] text-zinc-600">
                {user?.email}
              </p>
            </div>

            <button
              onClick={logout}
              title="Sign out"
              className="rounded-xl p-2 text-zinc-600 transition hover:bg-white/[0.06] hover:text-red-300"
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}
