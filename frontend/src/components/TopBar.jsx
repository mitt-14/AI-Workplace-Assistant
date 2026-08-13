import { Menu, Cpu, Command } from "lucide-react";
import StatusDot from "./StatusDot";

export default function TopBar({ onMenu }) {
  return (
    <header className="sticky top-0 z-20 border-b border-white/[0.06] bg-[#07080d]/75 backdrop-blur-2xl">
      <div className="mx-auto flex h-16 max-w-[1500px] items-center gap-3 px-4 sm:px-7 lg:px-10">
        <button className="btn-secondary p-2.5 lg:hidden" onClick={onMenu}>
          <Menu size={18} />
        </button>

        <div className="hidden items-center gap-2 text-xs text-zinc-500 sm:flex">
          <Command size={14} />
          <span>AI Workplace Assistant</span>
        </div>

        <div className="ml-auto flex items-center gap-2">
          <StatusDot label="Local backend" />
          <span className="hidden sm:inline-flex">
            <StatusDot label="Ollama" />
          </span>
          <div className="grid h-9 w-9 place-items-center rounded-xl border border-white/10 bg-white/[0.04] text-zinc-400">
            <Cpu size={16} />
          </div>
        </div>
      </div>
    </header>
  );
}
