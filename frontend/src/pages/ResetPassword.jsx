import { useState } from "react";
import {
  ArrowRight,
  KeyRound,
} from "lucide-react";

import AmbientBackground from "../components/AmbientBackground";
import PasswordStrength, {
  getPasswordChecks,
} from "../components/PasswordStrength";
import { useAuth } from "../context/AuthContext";

export default function ResetPassword({
  token,
  onComplete,
}) {
  const { resetPassword } = useAuth();

  const [password, setPassword] = useState(
    ""
  );
  const [confirm, setConfirm] = useState(
    ""
  );
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(
    false
  );

  async function submit(
    event,
  ) {
    event.preventDefault();
    setError("");

    if (
      password !== confirm
    ) {
      setError(
        "Passwords do not match."
      );
      return;
    }

    const checks = getPasswordChecks({
      password,
    });

    if (
      checks
        .slice(0, 6)
        .some(
          ([, valid]) => !valid
        )
    ) {
      setError(
        "Please satisfy the password security requirements."
      );
      return;
    }

    setLoading(true);

    try {
      await resetPassword(
        token,
        password,
      );

      onComplete();
    } catch (error) {
      setError(
        error.message
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="relative min-h-screen overflow-hidden text-zinc-100">
      <AmbientBackground />

      <div className="mx-auto grid min-h-screen max-w-7xl place-items-center px-5 py-10">
        <section className="w-full max-w-md">
          <div className="panel page-enter p-6 sm:p-8">
            <div className="mb-7">
              <div className="mb-5 grid h-12 w-12 place-items-center rounded-2xl bg-fuchsia-500/10 text-fuchsia-300">
                <KeyRound size={21} />
              </div>

              <h2 className="text-2xl font-bold tracking-tight">
                Choose a new password
              </h2>

              <p className="mt-2 text-sm leading-6 text-zinc-500">
                Your new password must satisfy the
                same strong policy used during
                registration.
              </p>
            </div>

            <form onSubmit={submit}>
              <label className="label">
                New password
              </label>

              <input
                className="input"
                type="password"
                required
                minLength={12}
                maxLength={128}
                autoComplete="new-password"
                value={password}
                onChange={
                  (event) =>
                    setPassword(
                      event.target.value
                    )
                }
                placeholder="New strong password"
              />

              <PasswordStrength
                password={password}
              />

              <label className="label mt-4">
                Confirm new password
              </label>

              <input
                className="input"
                type="password"
                required
                minLength={12}
                maxLength={128}
                autoComplete="new-password"
                value={confirm}
                onChange={
                  (event) =>
                    setConfirm(
                      event.target.value
                    )
                }
                placeholder="Repeat new password"
              />

              {error && (
                <div className="mt-4 rounded-2xl border border-red-900/40 bg-red-950/20 p-3 text-xs leading-5 text-red-300">
                  {error}
                </div>
              )}

              <button
                className="btn-primary mt-6 w-full"
                disabled={loading}
              >
                {loading
                  ? "Changing password…"
                  : "Change password"}
                <ArrowRight size={16} />
              </button>
            </form>
          </div>
        </section>
      </div>
    </div>
  );
}
