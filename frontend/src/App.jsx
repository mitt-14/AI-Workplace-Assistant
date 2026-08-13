import { useState } from "react";
import Sidebar from "./components/Sidebar";
import TopBar from "./components/TopBar";
import AmbientBackground from "./components/AmbientBackground";
import Dashboard from "./pages/Dashboard";
import Chat from "./pages/Chat";
import Documents from "./pages/Documents";
import EmailAssistant from "./pages/EmailAssistant";
import Meetings from "./pages/Meetings";
import Workflows from "./pages/Workflows";
import Agent from "./pages/Agent";
import Settings from "./pages/Settings";

const pages = {
  dashboard: Dashboard,
  chat: Chat,
  documents: Documents,
  email: EmailAssistant,
  meetings: Meetings,
  workflows: Workflows,
  agent: Agent,
  settings: Settings,
};

export default function App() {
  const [page, setPage] = useState("dashboard");
  const [menuOpen, setMenuOpen] = useState(false);
  const Page = pages[page];

  return (
    <div className="min-h-screen text-zinc-100">
      <AmbientBackground />

      <Sidebar
        page={page}
        setPage={setPage}
        open={menuOpen}
        setOpen={setMenuOpen}
      />

      <main className="lg:pl-[292px]">
        <TopBar onMenu={() => setMenuOpen(true)} />

        <div className="mx-auto max-w-[1500px] p-5 sm:p-7 lg:p-10">
          <div key={page} className="page-enter">
            <Page />
          </div>
        </div>

        <footer className="mx-auto max-w-[1500px] px-5 pb-8 text-center text-[11px] text-zinc-700 sm:px-7 lg:px-10">
          AI Workplace Assistant · Local-first portfolio system
        </footer>
      </main>
    </div>
  );
}
