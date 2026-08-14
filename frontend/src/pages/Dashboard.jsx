import { useEffect, useState } from "react";
import {
  Bell,
  Bot,
  CheckSquare,
  Workflow,
  ArrowUpRight,
  BrainCircuit,
  FileSearch,
  Sparkles,
} from "lucide-react";
import { api } from "../lib/api";
import PageHeader from "../components/PageHeader";

const statCards = [
  ["Tasks", CheckSquare, "tasks", "from-indigo-500/20 to-cyan-500/5"],
  ["Notifications", Bell, "notifications", "from-fuchsia-500/20 to-violet-500/5"],
  ["Workflow runs", Workflow, "executions", "from-emerald-500/20 to-cyan-500/5"],
  ["Agent tools", Bot, "tools", "from-amber-500/20 to-rose-500/5"],
];

const modules = [
  ["Knowledge Assistant", "Search and analyze workplace documents.", FileSearch],
  ["AI Document Analyzer", "Summaries, risks, action items and recommendations.", Sparkles],
  ["Multi-tool Agent", "Plan and execute across your workplace tools.", BrainCircuit],
];

function readCount(value) {
  if (typeof value?.total === "number") return value.total;
  if (typeof value?.count === "number") return value.count;
  if (Array.isArray(value)) return value.length;
  if (Array.isArray(value?.tasks)) return value.tasks.length;
  if (Array.isArray(value?.notifications)) return value.notifications.length;
  if (Array.isArray(value?.executions)) return value.executions.length;
  return "—";
}

export default function Dashboard() {
  const [stats, setStats] = useState({
    tasks: "—",
    notifications: "—",
    executions: "—",
    tools: "—",
  });

  useEffect(() => {
    Promise.allSettled([
      api.get("/tasks"),
      api.get("/notifications"),
      api.get("/workflows/executions"),
      api.get("/agents/tools"),
    ]).then(([tasks, notifications, executions, tools]) => {
      setStats({
        tasks: tasks.status === "fulfilled" ? readCount(tasks.value) : "—",
        notifications: notifications.status === "fulfilled" ? readCount(notifications.value) : "—",
        executions: executions.status === "fulfilled" ? readCount(executions.value) : "—",
        tools: tools.status === "fulfilled" ? readCount(tools.value) : "—",
      });
    });
  }, []);

  return (
    <>
      <PageHeader
        eyebrow="Command Center"
        title="Your workplace, amplified by AI"
        description="A local-first intelligence layer for company knowledge, communication, meetings, workflows and multi-step automation."
        action={
          <div className="badge border-emerald-400/20 bg-emerald-400/5 text-emerald-300">
            <span className="h-2 w-2 rounded-full bg-emerald-400" />
            All systems ready
          </div>
        }
      />

      <section className="relative mb-6 overflow-hidden rounded-[32px] border border-white/10 bg-gradient-to-br from-indigo-500/14 via-white/[0.045] to-fuchsia-500/10 p-6 shadow-2xl shadow-black/20 sm:p-8">
        <div className="absolute -right-14 -top-20 h-64 w-64 rounded-full bg-indigo-500/20 blur-3xl" />
        <div className="relative z-10 max-w-3xl">
          <span className="badge mb-5 border-indigo-400/20 bg-indigo-400/10 text-indigo-200">
            Unified AI Workspace
          </span>
          <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">
            One interface. Every AI capability.
          </h2>
          <p className="mt-3 max-w-2xl text-sm leading-7 text-zinc-400">
            Chat with models, explore documents, analyze email and meetings,
            inspect automations and hand complex goals to your agent — without
            leaving your local workspace.
          </p>
        </div>
      </section>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {statCards.map(([label, Icon, key, gradient], index) => (
          <div
            key={key}
            className={`panel-hover shine page-enter bg-gradient-to-br ${gradient} p-5`}
            style={{ animationDelay: `${index * 70}ms` }}
          >
            <div className="mb-7 flex items-center justify-between">
              <div className="grid h-10 w-10 place-items-center rounded-2xl bg-black/20 text-zinc-200">
                <Icon size={18} />
              </div>
              <ArrowUpRight size={16} className="text-zinc-600" />
            </div>
            <p className="text-3xl font-bold tracking-tight">{stats[key]}</p>
            <p className="mt-1 text-sm text-zinc-500">{label}</p>
          </div>
        ))}
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-[1.3fr_.7fr]">
        <section className="panel p-6">
          <div className="mb-6">
            <p className="text-sm font-semibold">Core intelligence</p>
            <p className="mt-1 text-xs text-zinc-500">
              The features that make this more than a chatbot.
            </p>
          </div>

          <div className="space-y-3">
            {modules.map(([title, description, Icon], index) => (
              <div
                key={title}
                className="group flex items-center gap-4 rounded-2xl border border-transparent p-4 transition hover:border-white/10 hover:bg-white/[0.035]"
              >
                <div className="grid h-11 w-11 shrink-0 place-items-center rounded-2xl bg-indigo-500/10 text-indigo-300 transition group-hover:scale-105">
                  <Icon size={19} />
                </div>
                <div>
                  <p className="text-sm font-semibold">{title}</p>
                  <p className="mt-1 text-xs leading-5 text-zinc-500">{description}</p>
                </div>
                <span className="ml-auto text-xs text-zinc-700">0{index + 1}</span>
              </div>
            ))}
          </div>
        </section>

        <section className="panel overflow-hidden p-6">
          <p className="text-sm font-semibold">Local stack</p>
          <div className="relative mt-6 space-y-5">
            {["React + Tailwind", "FastAPI", "Ollama / Gemini", "SQLite + ChromaDB"].map(
              (item, index) => (
                <div className="relative flex items-center gap-3" key={item}>
                  <div className="relative z-10 h-3 w-3 rounded-full border-2 border-indigo-400 bg-[#0c0d13]" />
                  {index < 3 && (
                    <div className="absolute left-[5px] top-4 h-8 w-px bg-gradient-to-b from-indigo-500/70 to-indigo-500/10" />
                  )}
                  <span className="text-sm text-zinc-400">{item}</span>
                </div>
              ),
            )}
          </div>
        </section>
      </div>
    </>
  );
}
