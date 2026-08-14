import { useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  KeyRound,
  Mail,
} from "lucide-react";

import AmbientBackground from "../components/AmbientBackground";
import { useAuth } from "../context/AuthContext";


export default function ForgotPassword({
  onLogin,
}) {
  const {
    forgotPassword,
  } = useAuth();

  const [
    email,
    setEmail,
  ] = useState("");

  const [
    submitted,
    setSubmitted,
  ] = useState(false);

  const [
    message,
    setMessage,
  ] = useState("");

  const [
    error,
    setError,
  ] = useState("");

  const [
    loading,
    setLoading,
  ] = useState(false);


  async function submit(event) {
    event.preventDefault();

    setLoading(true);
    setError("");

    try {
      const response = (
        await forgotPassword(
          email
        )
      );

      setMessage(
        response.message
      );

      setSubmitted(true);

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

            <button
              type="button"
              onClick={onLogin}
              className="mb-6 inline-flex items-center gap-2 text-xs text-zinc-500 transition hover:text-zinc-200"
            >
              <ArrowLeft size={14} />
              Back to sign in
            </button>

            {!submitted ? (
              <>
                <div className="mb-7">

                  <div className="mb-5 grid h-12 w-12 place-items-center rounded-2xl bg-indigo-500/10 text-indigo-300">
                    <KeyRound size={21} />
                  </div>

                  <h2 className="text-2xl font-bold tracking-tight">
                    Forgot password?
                  </h2>

                  <p className="mt-2 text-sm leading-6 text-zinc-500">
                    Enter your account email. If an
                    account exists, we will send a
                    secure password-reset link to
                    that mailbox.
                  </p>

                </div>

                <form onSubmit={submit}>

                  <label className="label">
                    Email
                  </label>

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
                      onChange={
                        (event) =>
                          setEmail(
                            event.target.value
                          )
                      }
                      placeholder="you@company.com"
                    />

                  </div>

                  {error && (
                    <div className="mt-4 rounded-2xl border border-red-900/40 bg-red-950/20 p-3 text-xs text-red-300">
                      {error}
                    </div>
                  )}

                  <button
                    className="btn-primary mt-6 w-full"
                    disabled={loading}
                  >
                    {loading
                      ? "Sending reset link…"
                      : "Send reset link"}

                    <ArrowRight size={16} />
                  </button>

                </form>
              </>
            ) : (
              <div className="text-center">

                <div className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-emerald-500/10 text-emerald-300">
                  <CheckCircle2 size={25} />
                </div>

                <h2 className="mt-5 text-2xl font-bold tracking-tight">
                  Check your email
                </h2>

                <p className="mt-3 text-sm leading-6 text-zinc-500">
                  {message}
                </p>

                <p className="mt-3 text-xs leading-5 text-zinc-600">
                  The link expires shortly and can
                  only be used once. Also check your
                  spam folder if you do not see it.
                </p>

                <button
                  type="button"
                  className="btn-secondary mt-6 w-full"
                  onClick={onLogin}
                >
                  Return to sign in
                </button>

              </div>
            )}

          </div>
        </section>
      </div>
    </div>
  );
}
