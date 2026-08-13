import { useState } from "react";
import { MailCheck, WandSparkles } from "lucide-react";
import { api } from "../lib/api";
import PageHeader from "../components/PageHeader";
import ResultCard from "../components/ResultCard";
import ProviderSelect from "../components/ProviderSelect";
import usePreferredProvider from "../hooks/usePreferredProvider";

export default function EmailAssistant() {
  const [provider, setProvider] = usePreferredProvider();
  const [form, setForm] = useState({
    subject: "",
    sender: "",
    recipients: "",
    body: "",
    generate_reply: true,
    reply_style: "professional",
  });
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function update(key, value) {
    setForm((old) => ({ ...old, [key]: value }));
  }

  async function submit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const result = await api.post("/email/analyze", {
        ...form,
        provider,
        recipients: form.recipients
          .split(",")
          .map((value) => value.trim())
          .filter(Boolean),
      });
      setResult(result);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="Communication Intelligence"
        title="Understand every email in seconds"
        description="Detect category, priority, sentiment, risk, deadlines and tasks — then generate a polished reply."
      />

      <div className="grid gap-6 xl:grid-cols-[.7fr_1.3fr]">
        <section className="panel p-5 sm:p-6">
          <div className="mb-6 grid h-12 w-12 place-items-center rounded-2xl bg-gradient-to-br from-fuchsia-500/20 to-violet-500/10 text-fuchsia-300">
            <WandSparkles size={21} />
          </div>
          <h2 className="font-semibold">Analysis controls</h2>
          <p className="mt-2 text-xs leading-5 text-zinc-500">
            Keep Ollama selected for a fully local experience.
          </p>

          <label className="label mt-6">Provider</label>
          <ProviderSelect value={provider} onChange={setProvider} />

          <label className="label mt-5">Reply style</label>
          <select
            className="input"
            value={form.reply_style}
            onChange={(event) => update("reply_style", event.target.value)}
          >
            <option value="professional">Professional</option>
            <option value="friendly">Friendly</option>
            <option value="formal">Formal</option>
            <option value="concise">Concise</option>
            <option value="detailed">Detailed</option>
          </select>

          <label className="mt-5 flex items-center gap-3 rounded-2xl border border-white/[0.07] bg-white/[0.025] p-4 text-sm text-zinc-300">
            <input
              className="accent-indigo-500"
              type="checkbox"
              checked={form.generate_reply}
              onChange={(event) => update("generate_reply", event.target.checked)}
            />
            Generate a suggested reply
          </label>
        </section>

        <form onSubmit={submit} className="panel p-5 sm:p-6">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="label">Subject</label>
              <input className="input" value={form.subject} onChange={(event) => update("subject", event.target.value)} />
            </div>
            <div>
              <label className="label">Sender</label>
              <input className="input" value={form.sender} onChange={(event) => update("sender", event.target.value)} />
            </div>
          </div>

          <label className="label mt-4">Recipients</label>
          <input
            className="input"
            value={form.recipients}
            onChange={(event) => update("recipients", event.target.value)}
            placeholder="team@company.com, manager@company.com"
          />

          <label className="label mt-4">Email body</label>
          <textarea
            className="input min-h-64 resize-none"
            required
            value={form.body}
            onChange={(event) => update("body", event.target.value)}
            placeholder="Paste an email here…"
          />

          <button className="btn-primary mt-5" disabled={loading}>
            <MailCheck size={17} />
            {loading ? "Analyzing email…" : "Analyze email"}
          </button>
        </form>
      </div>

      <div className="mt-6">
        <ResultCard result={result} error={error} loading={loading} />
      </div>
    </>
  );
}
