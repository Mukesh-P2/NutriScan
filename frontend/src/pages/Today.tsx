import { useEffect, useState } from "react";
import { useAuth } from "../AuthContext";
import Login from "./Login";
import { deleteConsumption, fetchHistory, fetchToday } from "../consumption";
import type { DailyProgress, DaySummary, NutrientProgress } from "../types";

function barColor(n: NutrientProgress): string {
  if (n.kind === "limit") return n.over ? "bg-rose-500" : "bg-slate-400";
  if (n.kind === "beneficial") return "bg-emerald-500"; // more is fine, even past target
  return n.over ? "bg-amber-500" : "bg-sky-500"; // budget: amber once over
}

function NutrientBar({ n }: { n: NutrientProgress }) {
  const width = Math.min(n.percent, 100);
  return (
    <div>
      <div className="flex justify-between text-sm">
        <span className="text-slate-600">
          {n.name}
          {n.kind === "limit" && <span className="ml-1 text-xs text-slate-400">(limit)</span>}
        </span>
        <span className={n.over ? (n.kind === "limit" ? "font-semibold text-rose-600" : "text-slate-800") : "text-slate-800"}>
          {n.consumed}/{n.target} {n.unit}
          {n.kind !== "limit" && !n.over && <span className="text-slate-400"> · {n.remaining} left</span>}
          {n.kind === "limit" && n.over && <span className="text-rose-500"> · over</span>}
        </span>
      </div>
      <div className="mt-1 h-2 overflow-hidden rounded-full bg-slate-100">
        <div className={`h-full rounded-full ${barColor(n)}`} style={{ width: `${width}%` }} />
      </div>
    </div>
  );
}

export default function Today() {
  const { user } = useAuth();
  const [progress, setProgress] = useState<DailyProgress | null>(null);
  const [history, setHistory] = useState<DaySummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    try {
      const [p, h] = await Promise.all([fetchToday(), fetchHistory(7)]);
      setProgress(p);
      setHistory(h.days);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (user) refresh();
  }, [user]);

  async function undo(id: number) {
    try {
      setProgress(await deleteConsumption(id));
      setHistory((await fetchHistory(7)).days);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to remove.");
    }
  }

  if (!user) return <Login />;
  if (loading) return <p className="text-slate-500">Loading…</p>;
  if (error) return <p className="rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{error}</p>;
  if (!progress) return null;

  const pct = progress.achievement_pct;
  const ringColor = pct >= 80 ? "#10b981" : pct >= 40 ? "#0ea5e9" : "#94a3b8";

  return (
    <div className="space-y-6">
      {/* Overall achievement */}
      <div className="flex items-center gap-6 rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <div
          className="flex h-28 w-28 shrink-0 items-center justify-center rounded-full"
          style={{ background: `conic-gradient(${ringColor} ${pct * 3.6}deg, #f1f5f9 0deg)` }}
        >
          <div className="flex h-20 w-20 flex-col items-center justify-center rounded-full bg-white">
            <span className="text-2xl font-bold text-slate-800">{pct}%</span>
            <span className="text-[10px] uppercase tracking-wide text-slate-400">day goal</span>
          </div>
        </div>
        <div>
          <h2 className="text-lg font-bold">Today's progress</h2>
          <p className="text-sm text-slate-500">
            {progress.calories_consumed} / {progress.calories_target} kcal
          </p>
          {!progress.targets_complete && (
            <p className="mt-1 text-xs text-amber-600">
              Using generic targets — complete your profile for personalized goals.
            </p>
          )}
        </div>
      </div>

      {/* Per-nutrient progress */}
      <div className="space-y-4 rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <h3 className="font-semibold text-slate-700">Nutrients</h3>
        {progress.nutrients.map((n) => (
          <NutrientBar key={n.name} n={n} />
        ))}
      </div>

      {/* Today's entries */}
      <div className="space-y-3 rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <h3 className="font-semibold text-slate-700">Logged today</h3>
        {progress.entries.length === 0 ? (
          <p className="text-sm text-slate-400">Nothing logged yet. Scan a product and tap “I ate this”.</p>
        ) : (
          <ul className="divide-y divide-slate-100">
            {progress.entries.map((e) => (
              <li key={e.id} className="flex items-center justify-between py-2 text-sm">
                <span className="text-slate-700">
                  {e.product_name} <span className="text-slate-400">· {e.servings} serving{e.servings === 1 ? "" : "s"} · {e.calories} kcal</span>
                </span>
                <button onClick={() => undo(e.id)} className="text-xs font-semibold text-slate-400 hover:text-rose-600">
                  Undo
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* 7-day history */}
      <div className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <h3 className="mb-3 font-semibold text-slate-700">Last 7 days</h3>
        <div className="flex items-end justify-between gap-2">
          {history.map((d) => (
            <div key={d.date} className="flex flex-1 flex-col items-center gap-1">
              <div className="flex h-24 w-full items-end">
                <div
                  className="w-full rounded-t bg-emerald-400"
                  style={{ height: `${Math.max(d.achievement_pct, 2)}%` }}
                  title={`${d.achievement_pct}% · ${d.calories_consumed} kcal · ${d.entries} item(s)`}
                />
              </div>
              <span className="text-[10px] text-slate-500">{d.achievement_pct}%</span>
              <span className="text-[10px] text-slate-400">{d.date.slice(5)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
