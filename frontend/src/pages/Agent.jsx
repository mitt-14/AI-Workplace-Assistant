import { useState } from "react";
import { Bot, Play, BrainCircuit, Route, Wrench } from "lucide-react";
import { api } from "../lib/api";
import PageHeader from "../components/PageHeader";
import ResultCard from "../components/ResultCard";
import ProviderSelect from "../components/ProviderSelect";
import usePreferredProvider from "../hooks/usePreferredProvider";

const examples = [
  {
    label: "Review tasks",
    instruction: "Show me my stored tasks and summarize what I should work on.",
    context: {},
  },
  {
    label: "Analyze email",
    instruction: "Analyze this email and tell me what needs action.",
    context: {
      subject: "Security report",
      body: "Please prepare the updated security report by Friday.",
    },
  },
];

export default function Agent() {
  const [instruction, setInstruction] = useState("");
  const [context, setContext] = useState("{}");
  const [provider, setProvider] = usePreferredProvider();
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function applyExample(example) {
    setInstruction(example.instruction);
    setContext(JSON.stringify(example.context, null, 2));
  }

  async function run(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);

    try {
      let parsed;
      try {
        parsed = JSON.parse(context || "{}");
      } catch {
        throw new Error("Context must be valid JSON.");
      }

      setResult(
        await api.post("/agents/run", {
          instruction,
          provider,
          max_steps: 5,
          context: parsed,
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
        eyebrow="Autonomous Workspace"
        title="Give your agent a goal"
        description="The agent plans, selects allowlisted tools, executes them and returns a practical answer — all on top of your existing modules."
      />

      <div className="mb-6 grid gap-4 md:grid-cols-3">
        {[
          ["Plan", "Turns your goal into safe executable steps.", Route],
          ["Act", "Uses document, email, meeting and workflow tools.", Wrench],
          ["Answer", "Synthesizes completed tool results.", BrainCircuit],
        ].map(([title, text, Icon]) => (
          <div className="panel-hover p-4" key={title}>
            <Icon size={18} className="mb-3 text-indigo-300" />
            <p className="text-sm font-semibold">{title}</p>
            <p className="mt-1 text-xs leading-5 text-zinc-500">{text}</p>
          </div>
        ))}
      </div>

      <form onSubmit={run} className="panel p-5 sm:p-6">
        <div className="mb-5 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <div className="grid h-12 w-12 place-items-center rounded-2xl bg-gradient-to-br from-indigo-500 to-fuchsia-500 shadow-lg shadow-fuchsia-950/30">
              <Bot size={21} />
            </div>
            <div>
              <p className="font-semibold">Multi-tool Agent</p>
              <p className="text-xs text-emerald-400">● Tool registry available</p>
            </div>
          </div>
          <ProviderSelect
            className="max-w-48"
            value={provider}
            onChange={setProvider}
          />
        </div>

        <div className="mb-4 flex flex-wrap gap-2">
          {examples.map((example) => (
            <button
              type="button"
              key={example.label}
              className="rounded-full border border-white/10 bg-white/[0.035] px-3 py-1.5 text-xs text-zinc-400 transition hover:border-indigo-400/30 hover:text-zinc-200"
              onClick={() => applyExample(example)}
            >
              {example.label}
            </button>
          ))}
        </div>

        <label className="label">Instruction</label>
        <textarea
          className="input min-h-36 resize-none"
          required
          value={instruction}
          onChange={(event) => setInstruction(event.target.value)}
          placeholder="Analyze this company document and tell me the most important risks."
        />

        <label className="label mt-5">Structured context</label>
        <textarea
          className="input min-h-52 resize-y font-mono text-xs leading-6"
          value={context}
          onChange={(event) => setContext(event.target.value)}
        />

        <button className="btn-primary mt-5" disabled={loading}>
          <Play size={17} />
          {loading ? "Agent is working…" : "Run agent"}
        </button>
      </form>

      <div className="mt-6">
        <ResultCard
          title="Agent execution"
          result={result}
          error={error}
          loading={loading}
        />
      </div>
    </>
  );
}
