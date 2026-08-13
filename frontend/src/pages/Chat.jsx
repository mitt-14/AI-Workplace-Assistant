import { useState } from "react";
import { Bot, Send, User, WandSparkles } from "lucide-react";
import { api } from "../lib/api";
import PageHeader from "../components/PageHeader";
import ProviderSelect from "../components/ProviderSelect";
import usePreferredProvider from "../hooks/usePreferredProvider";

const suggestions = [
  "Explain our AI architecture.",
  "Give me a concise security checklist.",
  "Summarize the key modules in this project.",
];

export default function Chat() {
  const [message, setMessage] = useState("");
  const [provider, setProvider] = usePreferredProvider();
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  async function submit(event, directText) {
    event?.preventDefault();
    const text = (directText ?? message).trim();
    if (!text || loading) return;

    setMessages((old) => [...old, { role: "user", text }]);
    setMessage("");
    setLoading(true);

    try {
      const result = await api.post("/chat", {
        message: text,
        provider,
      });

      const answer =
        result?.response ??
        result?.answer ??
        JSON.stringify(result, null, 2);

      setMessages((old) => [
        ...old,
        { role: "assistant", text: answer },
      ]);
    } catch (error) {
      setMessages((old) => [
        ...old,
        { role: "assistant", text: `Error: ${error.message}` },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="Assistant"
        title="Talk to your AI workspace"
        description="Fast, local conversations through Ollama — with Gemini available when configured."
      />

      <div className="panel overflow-hidden">
        <div className="flex items-center justify-between border-b border-white/[0.07] p-4 sm:p-5">
          <div className="flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 shadow-lg shadow-indigo-950/40">
              <Bot size={19} />
            </div>
            <div>
              <p className="text-sm font-semibold">Workplace Copilot</p>
              <p className="text-[11px] text-emerald-400">● Ready</p>
            </div>
          </div>
          <ProviderSelect
            className="max-w-[165px]"
            value={provider}
            onChange={setProvider}
          />
        </div>

        <div className="min-h-[560px] space-y-5 overflow-y-auto p-4 sm:p-6">
          {messages.length === 0 && (
            <div className="grid min-h-[450px] place-items-center">
              <div className="max-w-xl text-center">
                <div className="mx-auto grid h-16 w-16 place-items-center rounded-[22px] border border-indigo-400/20 bg-indigo-500/10 text-indigo-300 shadow-glow">
                  <WandSparkles size={27} />
                </div>
                <h2 className="mt-5 text-xl font-semibold">What can I help with?</h2>
                <p className="mt-2 text-sm leading-6 text-zinc-500">
                  Start with a question or pick one of these.
                </p>
                <div className="mt-6 flex flex-wrap justify-center gap-2">
                  {suggestions.map((suggestion) => (
                    <button
                      key={suggestion}
                      className="rounded-full border border-white/10 bg-white/[0.035] px-4 py-2 text-xs text-zinc-400 transition hover:border-indigo-400/30 hover:text-zinc-200"
                      onClick={(event) => submit(event, suggestion)}
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {messages.map((item, index) => (
            <div
              key={index}
              className={`page-enter flex gap-3 ${
                item.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              {item.role === "assistant" && (
                <div className="mt-1 grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-indigo-500/15 text-indigo-300">
                  <Bot size={15} />
                </div>
              )}
              <div
                className={`max-w-[82%] whitespace-pre-wrap rounded-3xl px-4 py-3 text-sm leading-7 ${
                  item.role === "user"
                    ? "rounded-tr-lg bg-gradient-to-br from-indigo-500 to-violet-600 text-white"
                    : "rounded-tl-lg border border-white/[0.07] bg-white/[0.045] text-zinc-300"
                }`}
              >
                {item.text}
              </div>
              {item.role === "user" && (
                <div className="mt-1 grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-white/[0.07] text-zinc-300">
                  <User size={15} />
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex items-center gap-3 text-xs text-zinc-500">
              <div className="flex gap-1">
                {[0, 1, 2].map((dot) => (
                  <span
                    key={dot}
                    className="h-1.5 w-1.5 animate-bounce rounded-full bg-indigo-400"
                    style={{ animationDelay: `${dot * 120}ms` }}
                  />
                ))}
              </div>
              Thinking locally…
            </div>
          )}
        </div>

        <form
          onSubmit={submit}
          className="border-t border-white/[0.07] bg-black/10 p-4"
        >
          <div className="flex gap-3">
            <textarea
              rows={1}
              className="input min-h-[50px] resize-none"
              placeholder="Message your workplace assistant…"
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  submit(event);
                }
              }}
            />
            <button className="btn-primary self-end" disabled={loading}>
              <Send size={17} />
              <span className="hidden sm:inline">Send</span>
            </button>
          </div>
        </form>
      </div>
    </>
  );
}
