import { useState } from "react";
import {
  ArrowRight,
  BrainCircuit,
  LockKeyhole,
  Mail,
  Sparkles,
} from "lucide-react";

import AmbientBackground from "../components/AmbientBackground";
import { useAuth } from "../context/AuthContext";

export default function Login({ onRegister }) {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      await login(email, password);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="relative min-h-screen overflow-hidden text-zinc-100">
      <AmbientBackground />

      <div className="mx-auto grid min-h-screen max-w-7xl items-center gap-12 px-5 py-10 lg:grid-cols-2 lg:px-10">
        <section className="hidden lg:block">
          <div className="badge mb-6 border-indigo-400/20 bg-indigo-400/10 text-indigo-200">
            <Sparkles size={13} />
            Phase 14 · Secure Workspace
          </div>

          <h1 className="max-w-xl bg-gradient-to-r from-white via-zinc-100 to-zinc-500 bg-clip-text text-6xl font-bold leading-[1.04] tracking-tight text-transparent">
            Your AI workplace.
            <br />
            Now personal.
          </h1>

          <p className="mt-6 max-w-lg text-base leading-8 text-zinc-500">
            Sign in to your local-first command center for documents,
            communication, meetings, workflows and autonomous agents.
          </p>

          <div className="mt-10 flex items-center gap-4 text-sm text-zinc-500">
            <div className="grid h-12 w-12 place-items-center rounded-2xl bg-indigo-500/10 text-indigo-300">
              <BrainCircuit size={21} />
            </div>
            FastAPI authentication · bcrypt · JWT · SQLite
          </div>
        </section>

        <section className="mx-auto w-full max-w-md">
          <div className="panel page-enter p-6 sm:p-8">
            <div className="mb-8">
              <div className="mb-5 grid h-12 w-12 place-items-center rounded-2xl bg-gradient-to-br from-indigo-500 via-violet-500 to-fuchsia-500 shadow-lg shadow-violet-950/40">
                <LockKeyhole size={21} />
              </div>
              <h2 className="text-2xl font-bold tracking-tight">
                Welcome back
              </h2>
              <p className="mt-2 text-sm text-zinc-500">
                Sign in to continue to AI Workplace Assistant.
              </p>
            </div>

            <form onSubmit={submit}>
              <label className="label">Email</label>
              <div className="relative">
                <Mail
                  size={16}
                  className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-600"
                />
                <input
                  className="input pl-11"
                  type="email"
                  required
                  autoComplete="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="you@company.com"
                />
              </div>

              <label className="label mt-5">Password</label>
              <input
                className="input"
                type="password"
                required
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Your password"
              />

              {error && (
                <div className="mt-4 rounded-2xl border border-red-900/40 bg-red-950/20 p-3 text-xs text-red-300">
                  {error}
                </div>
              )}

              <button
                className="btn-primary mt-6 w-full"
                disabled={loading}
              >
                {loading ? "Signing in…" : "Sign in"}
                <ArrowRight size={16} />
              </button>
            </form>

            <p className="mt-6 text-center text-xs text-zinc-600">
              New here?{" "}
              <button
                type="button"
                onClick={onRegister}
                className="font-semibold text-indigo-300 transition hover:text-indigo-200"
              >
                Create an account
              </button>
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}
