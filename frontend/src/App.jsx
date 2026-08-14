import { useState } from "react";

import AmbientBackground from "./components/AmbientBackground";
import Sidebar from "./components/Sidebar";
import TopBar from "./components/TopBar";
import { useAuth } from "./context/AuthContext";
import Agent from "./pages/Agent";
import Chat from "./pages/Chat";
import Dashboard from "./pages/Dashboard";
import Documents from "./pages/Documents";
import EmailAssistant from "./pages/EmailAssistant";
import ForgotPassword from "./pages/ForgotPassword";
import Login from "./pages/Login";
import Meetings from "./pages/Meetings";
import Register from "./pages/Register";
import ResetPassword from "./pages/ResetPassword";
import Settings from "./pages/Settings";
import Workflows from "./pages/Workflows";

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


function initialResetToken() {
  return (
    new URLSearchParams(
      window.location.search
    ).get("reset_token")
    || ""
  );
}


export default function App() {
  const {
    authenticated,
    loading,
  } = useAuth();

  const initialToken = (
    initialResetToken()
  );

  const [
    authScreen,
    setAuthScreen,
  ] = useState(
    initialToken
      ? "reset"
      : "login"
  );

  const [
    resetToken,
    setResetToken,
  ] = useState(
    initialToken
  );

  const [page, setPage] = useState(
    "dashboard"
  );

  const [
    menuOpen,
    setMenuOpen,
  ] = useState(false);

  function finishReset() {
    setResetToken("");
    setAuthScreen("login");

    window.history.replaceState(
      {},
      "",
      "/",
    );
  }

  if (loading) {
    return (
      <div className="relative grid min-h-screen place-items-center text-zinc-100">
        <AmbientBackground />

        <div className="text-center">
          <div className="mx-auto h-9 w-9 animate-spin rounded-full border-2 border-white/10 border-t-indigo-400" />

          <p className="mt-4 text-xs text-zinc-500">
            Restoring secure session…
          </p>
        </div>
      </div>
    );
  }

  if (!authenticated) {
    if (
      authScreen === "reset"
      && resetToken
    ) {
      return (
        <ResetPassword
          token={resetToken}
          onComplete={finishReset}
        />
      );
    }

    if (
      authScreen === "forgot"
    ) {
      return (
        <ForgotPassword
          onLogin={
            () =>
              setAuthScreen(
                "login"
              )
          }
        />
      );
    }

    if (
      authScreen === "register"
    ) {
      return (
        <Register
          onLogin={
            () =>
              setAuthScreen(
                "login"
              )
          }
        />
      );
    }

    return (
      <Login
        onRegister={
          () =>
            setAuthScreen(
              "register"
            )
        }
        onForgot={
          () =>
            setAuthScreen(
              "forgot"
            )
        }
      />
    );
  }

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
        <TopBar
          onMenu={
            () =>
              setMenuOpen(true)
          }
        />

        <div className="mx-auto max-w-[1500px] p-5 sm:p-7 lg:p-10">
          <div
            key={page}
            className="page-enter"
          >
            <Page />
          </div>
        </div>

        <footer className="mx-auto max-w-[1500px] px-5 pb-8 text-center text-[11px] text-zinc-700 sm:px-7 lg:px-10">
          AI Workplace Assistant ·
          Secure local-first portfolio system
        </footer>
      </main>
    </div>
  );
}
