import { Copy, Check } from "lucide-react";
import { useState } from "react";

export default function JsonView({ value }) {
  const [copied, setCopied] = useState(false);

  if (value == null) return null;

  const text = JSON.stringify(value, null, 2);

  async function copy() {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1000);
  }

  return (
    <div className="relative">
      <button
        className="absolute right-3 top-3 z-10 rounded-xl border border-white/10 bg-zinc-950/80 p-2 text-zinc-400 transition hover:text-white"
        onClick={copy}
        type="button"
      >
        {copied ? <Check size={15} /> : <Copy size={15} />}
      </button>

      <pre className="max-h-[560px] overflow-auto rounded-2xl border border-white/10 bg-black/30 p-5 pr-12 text-xs leading-6 text-zinc-300">
        {text}
      </pre>
    </div>
  );
}
