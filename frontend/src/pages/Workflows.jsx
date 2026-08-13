import { useEffect, useState } from "react";
import {
  RefreshCw,
  Bell,
  CheckSquare,
  Workflow as WorkflowIcon,
  Zap,
} from "lucide-react";
import { api } from "../lib/api";
import PageHeader from "../components/PageHeader";
import JsonView from "../components/JsonView";

const views = {
  tasks: ["/tasks", CheckSquare],
  notifications: ["/notifications", Bell],
  executions: ["/workflows/executions", WorkflowIcon],
};

export default function Workflows() {
  const [tab, setTab] = useState("tasks");
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function load(selected = tab) {
    setLoading(true);
    setError("");
    try {
      setData(await api.get(views[selected][0]));
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load(tab);
  }, [tab]);

  return (
    <>
      <PageHeader
        eyebrow="Automation Engine"
        title="Workflows that keep moving"
        description="Review tasks, notifications and execution history produced by your local automation engine."
        action={
          <div className="badge border-amber-400/20 bg-amber-400/5 text-amber-300">
            <Zap size={13} />
            SQLite persistence
          </div>
        }
      />

      <section className="panel overflow-hidden">
        <div className="flex flex-wrap items-center gap-2 border-b border-white/[0.07] p-4">
          {Object.entries(views).map(([item, [, Icon]]) => (
            <button
              key={item}
              onClick={() => setTab(item)}
              className={tab === item ? "btn-primary" : "btn-secondary"}
            >
              <Icon size={16} />
              {item[0].toUpperCase() + item.slice(1)}
            </button>
          ))}

          <button
            onClick={() => load()}
            className="btn-secondary ml-auto"
          >
            <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
            Refresh
          </button>
        </div>

        <div className="min-h-[480px] p-5 sm:p-6">
          {loading && (
            <div className="grid min-h-72 place-items-center text-sm text-zinc-500">
              Loading workflow data…
            </div>
          )}
          {error && (
            <div className="rounded-2xl border border-red-900/50 bg-red-950/20 p-4 text-sm text-red-300">
              {error}
            </div>
          )}
          {!loading && !error && <JsonView value={data} />}
        </div>
      </section>
    </>
  );
}
