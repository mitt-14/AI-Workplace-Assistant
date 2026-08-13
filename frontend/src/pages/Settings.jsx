import { useState } from "react";
import { API_BASE_URL } from "../lib/api";
import PageHeader from "../components/PageHeader";
import usePreferredProvider from "../hooks/usePreferredProvider";
import ProviderSelect from "../components/ProviderSelect";
import { HardDrive, Server, ShieldCheck } from "lucide-react";

export default function Settings() {
  const [provider, setProvider] = usePreferredProvider();

  return (
    <>
      <PageHeader
        eyebrow="Local Configuration"
        title="Settings without exposing secrets"
        description="Frontend preferences stay in your browser; model credentials and backend configuration remain safely in backend/.env."
      />

      <div className="grid gap-6 xl:grid-cols-2">
        <section className="panel p-6">
          <h2 className="font-semibold">Experience</h2>
          <label className="label mt-6">Preferred provider</label>
          <ProviderSelect value={provider} onChange={setProvider} />

          <label className="label mt-5">FastAPI base URL</label>
          <div className="rounded-2xl border border-white/[0.07] bg-black/20 p-4 font-mono text-xs text-zinc-500">
            {API_BASE_URL}
          </div>
        </section>

        <section className="panel p-6">
          <h2 className="font-semibold">Privacy architecture</h2>
          <div className="mt-5 space-y-3">
            {[
              [HardDrive, "Local data", "SQLite, ChromaDB and uploads remain on your machine."],
              [Server, "Local AI", "Ollama can run the core assistant without cloud inference."],
              [ShieldCheck, "Secret separation", "API keys stay in backend/.env, not in React."],
            ].map(([Icon, title, text]) => (
              <div className="flex gap-3 rounded-2xl border border-white/[0.06] bg-white/[0.025] p-4" key={title}>
                <Icon size={18} className="mt-0.5 shrink-0 text-indigo-300" />
                <div>
                  <p className="text-sm font-medium">{title}</p>
                  <p className="mt-1 text-xs leading-5 text-zinc-500">{text}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </>
  );
}
