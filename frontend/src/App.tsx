import { useState } from "react";
import Scan from "./pages/Scan";
import Ask from "./pages/Ask";
import Lookup from "./pages/Lookup";
import Today from "./pages/Today";
import Profile from "./pages/Profile";
import { useAuth } from "./AuthContext";

type Tab = "scan" | "ask" | "lookup" | "today" | "profile";

export default function App() {
  const [tab, setTab] = useState<Tab>("scan");
  const { user } = useAuth();

  const tabClass = (t: Tab) =>
    `rounded-md px-4 py-1.5 ${tab === t ? "bg-white text-emerald-700 shadow-sm" : "text-slate-500"}`;

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-2xl items-center justify-between px-4 py-4">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🥗</span>
            <h1 className="text-xl font-bold text-emerald-700">NutriScan</h1>
          </div>
          <nav className="flex gap-1 rounded-lg bg-slate-100 p-1 text-sm font-medium">
            <button onClick={() => setTab("scan")} className={tabClass("scan")}>Scan</button>
            <button onClick={() => setTab("ask")} className={tabClass("ask")}>Ask</button>
            <button onClick={() => setTab("lookup")} className={tabClass("lookup")}>Lookup</button>
            <button onClick={() => setTab("today")} className={tabClass("today")}>Today</button>
            <button onClick={() => setTab("profile")} className={tabClass("profile")}>
              {user ? "👤 " + (user.name || "Profile") : "Log in"}
            </button>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-2xl px-4 py-6">
        {tab === "scan" && <Scan />}
        {tab === "ask" && <Ask />}
        {tab === "lookup" && <Lookup />}
        {tab === "today" && <Today />}
        {tab === "profile" && <Profile />}
      </main>
    </div>
  );
}
