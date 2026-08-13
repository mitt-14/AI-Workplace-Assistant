import { useState } from "react";
import { Users, AudioLines, Sparkles } from "lucide-react";
import { api } from "../lib/api";
import PageHeader from "../components/PageHeader";
import ResultCard from "../components/ResultCard";
import ProviderSelect from "../components/ProviderSelect";
import usePreferredProvider from "../hooks/usePreferredProvider";

export default function Meetings() {
  const [title, setTitle] = useState("");
  const [transcript, setTranscript] = useState("");
  const [provider, setProvider] = usePreferredProvider();
  const [followUp, setFollowUp] = useState(true);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);

    try {
      setResult(
        await api.post("/meetings/analyze", {
          title,
          transcript,
          provider,
          generate_follow_up_email: followUp,
          follow_up_email_style: "professional",
        }),
      );
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="Meeting Intelligence"
        title="Transform conversation into action"
        description="Extract decisions, owners, deadlines and follow-up items from meeting transcripts."
      />

      <form onSubmit={submit} className="panel overflow-hidden">
        <div className="border-b border-white/[0.07] bg-gradient-to-r from-cyan-500/[0.06] to-indigo-500/[0.05] p-5 sm:p-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-center">
            <div className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-cyan-500/10 text-cyan-300">
              <AudioLines size={22} />
            </div>
            <div className="flex-1">
              <label className="label">Meeting title</label>
              <input
                className="input"
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                placeholder="Security Project Weekly Meeting"
              />
            </div>
            <div className="w-full md:w-48">
              <label className="label">Provider</label>
              <ProviderSelect value={provider} onChange={setProvider} />
            </div>
          </div>
        </div>

        <div className="p-5 sm:p-6">
          <label className="label">Transcript</label>
          <textarea
            className="input min-h-[360px] resize-y"
            required
            value={transcript}
            onChange={(event) => setTranscript(event.target.value)}
            placeholder={"Alice: Good morning everyone...\nMiten: I will complete the report by Friday..."}
          />

          <div className="mt-5 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <label className="flex items-center gap-3 text-sm text-zinc-400">
              <input
                className="accent-indigo-500"
                type="checkbox"
                checked={followUp}
                onChange={(event) => setFollowUp(event.target.checked)}
              />
              Generate follow-up email
            </label>

            <button className="btn-primary" disabled={loading}>
              <Sparkles size={17} />
              {loading ? "Analyzing meeting…" : "Analyze meeting"}
            </button>
          </div>
        </div>
      </form>

      <div className="mt-6">
        <ResultCard result={result} error={error} loading={loading} />
      </div>
    </>
  );
}
