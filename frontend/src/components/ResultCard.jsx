import { AlertTriangle, Sparkles } from "lucide-react";
import JsonView from "./JsonView";

export default function ResultCard({
  title = "Result",
  result,
  error,
  loading = false,
}) {
  if (!result && !error && !loading) return null;

  return (
    <section className="panel page-enter p-5 sm:p-6">
      <div className="mb-5 flex items-center gap-3">
        <div className="grid h-9 w-9 place-items-center rounded-xl bg-indigo-500/15 text-indigo-300">
          <Sparkles size={17} />
        </div>
        <h3 className="font-semibold">{title}</h3>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[100, 82, 92, 66].map((width, index) => (
            <div
              key={index}
              className="h-4 animate-pulse rounded-full bg-white/5"
              style={{ width: `${width}%` }}
            />
          ))}
        </div>
      ) : error ? (
        <div className="flex gap-3 rounded-2xl border border-red-900/50 bg-red-950/25 p-4 text-sm text-red-200">
          <AlertTriangle className="mt-0.5 shrink-0" size={18} />
          {error}
        </div>
      ) : (
        <JsonView value={result} />
      )}
    </section>
  );
}
