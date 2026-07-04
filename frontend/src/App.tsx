import { useState } from "react";
import Scan from "./pages/Scan";
import Ask from "./pages/Ask";

type Tab = "scan" | "ask";

export default function App() {
  const [tab, setTab] = useState<Tab>("scan");

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-2xl items-center justify-between px-4 py-4">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🥗</span>
            <h1 className="text-xl font-bold text-emerald-700">NutriScan</h1>
          </div>
          <nav className="flex gap-1 rounded-lg bg-slate-100 p-1 text-sm font-medium">
            <button
              onClick={() => setTab("scan")}
              className={`rounded-md px-4 py-1.5 ${tab === "scan" ? "bg-white text-emerald-700 shadow-sm" : "text-slate-500"}`}
            >
              Scan
            </button>
            <button
              onClick={() => setTab("ask")}
              className={`rounded-md px-4 py-1.5 ${tab === "ask" ? "bg-white text-emerald-700 shadow-sm" : "text-slate-500"}`}
            >
              Ask
            </button>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-2xl px-4 py-6">{tab === "scan" ? <Scan /> : <Ask />}</main>
    </div>
  );
}
