import {
  HardDrive,
  Server,
  ShieldCheck,
  UserRound,
} from "lucide-react";

import PageHeader from "../components/PageHeader";
import ProviderSelect from "../components/ProviderSelect";
import { useAuth } from "../context/AuthContext";
import usePreferredProvider from "../hooks/usePreferredProvider";
import { API_BASE_URL } from "../lib/api";

export default function Settings() {
  const [provider, setProvider] = usePreferredProvider();
  const { user } = useAuth();

  return (
    <>
      <PageHeader
        eyebrow="Secure Configuration"
        title="Your workspace settings"
        description="Identity and frontend preferences stay separated from backend secrets and model credentials."
      />

      <div className="grid gap-6 xl:grid-cols-2">
        <section className="panel p-6">
          <div className="flex items-center gap-3">
            <div className="grid h-11 w-11 place-items-center rounded-2xl bg-indigo-500/10 text-indigo-300">
              <UserRound size={19} />
            </div>
            <div>
              <h2 className="font-semibold">{user?.name}</h2>
              <p className="text-xs text-zinc-500">{user?.email}</p>
            </div>
          </div>

          <label className="label mt-7">Preferred provider</label>
          <ProviderSelect value={provider} onChange={setProvider} />

          <label className="label mt-5">FastAPI base URL</label>
          <div className="rounded-2xl border border-white/[0.07] bg-black/20 p-4 font-mono text-xs text-zinc-500">
            {API_BASE_URL}
          </div>
        </section>

        <section className="panel p-6">
          <h2 className="font-semibold">Security architecture</h2>

          <div className="mt-5 space-y-3">
            {[
              [
                HardDrive,
                "Local identity store",
                "Users are persisted in a local SQLite database.",
              ],
              [
                Server,
                "JWT sessions",
                "The frontend authenticates with expiring bearer tokens.",
              ],
              [
                ShieldCheck,
                "Password protection",
                "Passwords are one-way hashed with bcrypt and are never stored as plaintext.",
              ],
            ].map(([Icon, title, text]) => (
              <div
                className="flex gap-3 rounded-2xl border border-white/[0.06] bg-white/[0.025] p-4"
                key={title}
              >
                <Icon
                  size={18}
                  className="mt-0.5 shrink-0 text-indigo-300"
                />
                <div>
                  <p className="text-sm font-medium">{title}</p>
                  <p className="mt-1 text-xs leading-5 text-zinc-500">
                    {text}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </>
  );
}
