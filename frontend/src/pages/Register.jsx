import { useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

import AmbientBackground from "../components/AmbientBackground";
import { useAuth } from "../context/AuthContext";

export default function Register({ onLogin }) {
  const { register } = useAuth();
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    confirm: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function update(key, value) {
    setForm((old) => ({ ...old, [key]: value }));
  }

  async function submit(event) {
    event.preventDefault();
    setError("");

    if (form.password !== form.confirm) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);

    try {
      await register(
        form.name,
        form.email,
        form.password,
      );
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
          <div className="badge mb-6 border-fuchsia-400/20 bg-fuchsia-400/10 text-fuchsia-200">
            <Sparkles size={13} />
            Local-first identity
          </div>

          <h1 className="max-w-xl text-6xl font-bold leading-[1.04] tracking-tight">
            One account.
            <br />
            <span className="bg-gradient-to-r from-indigo-300 via-violet-300 to-fuchsia-300 bg-clip-text text-transparent">
              Your entire AI stack.
            </span>
          </h1>

          <p className="mt-6 max-w-lg text-base leading-8 text-zinc-500">
            Your password is hashed before storage and your local
            workspace remains under your control.
          </p>
        </section>

        <section className="mx-auto w-full max-w-md">
          <div className="panel page-enter p-6 sm:p-8">
            <button
              type="button"
              onClick={onLogin}
              className="mb-6 inline-flex items-center gap-2 text-xs text-zinc-500 transition hover:text-zinc-200"
            >
              <ArrowLeft size={14} />
              Back to sign in
            </button>

            <div className="mb-7">
              <div className="mb-5 grid h-12 w-12 place-items-center rounded-2xl bg-emerald-500/10 text-emerald-300">
                <ShieldCheck size={22} />
              </div>
              <h2 className="text-2xl font-bold tracking-tight">
                Create your workspace
              </h2>
              <p className="mt-2 text-sm text-zinc-500">
                Set up your local AI Workplace account.
              </p>
            </div>

            <form onSubmit={submit}>
              <label className="label">Name</label>
              <input
                className="input"
                required
                minLength={2}
                value={form.name}
                onChange={(event) => update("name", event.target.value)}
                placeholder="Your name"
              />

              <label className="label mt-4">Email</label>
              <input
                className="input"
                type="email"
                required
                autoComplete="email"
                value={form.email}
                onChange={(event) => update("email", event.target.value)}
                placeholder="you@company.com"
              />

              <label className="label mt-4">Password</label>
              <input
                className="input"
                type="password"
                required
                minLength={8}
                autoComplete="new-password"
                value={form.password}
                onChange={(event) => update("password", event.target.value)}
                placeholder="Minimum 8 characters"
              />

              <label className="label mt-4">Confirm password</label>
              <input
                className="input"
                type="password"
                required
                minLength={8}
                autoComplete="new-password"
                value={form.confirm}
                onChange={(event) => update("confirm", event.target.value)}
                placeholder="Repeat your password"
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
                {loading ? "Creating account…" : "Create account"}
                <ArrowRight size={16} />
              </button>
            </form>
          </div>
        </section>
      </div>
    </div>
  );
}
