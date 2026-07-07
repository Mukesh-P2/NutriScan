import { useState } from "react";
import { getScanHistory } from "../scanHistory";
import type { AnalysisResult, ServingNutrition, Verdict } from "../types";

const verdictStyle: Record<Verdict, string> = {
  healthy: "bg-emerald-100 text-emerald-800",
  moderate: "bg-amber-100 text-amber-800",
  unhealthy: "bg-rose-100 text-rose-800",
};

// Direction of "better" per metric: higher protein/fiber is good, lower sugar/sat-fat/sodium is good.
const METRICS: { key: keyof ServingNutrition; label: string; unit: string; better: "high" | "low" | "none" }[] = [
  { key: "calories", label: "Calories", unit: "kcal", better: "none" },
  { key: "protein_g", label: "Protein", unit: "g", better: "high" },
  { key: "fiber_g", label: "Fiber", unit: "g", better: "high" },
  { key: "carbs_g", label: "Carbs", unit: "g", better: "none" },
  { key: "sugar_g", label: "Sugars", unit: "g", better: "low" },
  { key: "fat_g", label: "Fat", unit: "g", better: "none" },
  { key: "saturated_fat_g", label: "Saturated fat", unit: "g", better: "low" },
  { key: "sodium_mg", label: "Sodium", unit: "mg", better: "low" },
];

const round1 = (v: number) => Math.round(v * 10) / 10;

// Which side wins for a metric — returns 'a', 'b', or 'tie'. "high"/"low" set the direction.
function winner(a: number, b: number, better: "high" | "low" | "none"): "a" | "b" | "tie" {
  if (better === "none" || a === b) return "tie";
  if (better === "high") return a > b ? "a" : "b";
  return a < b ? "a" : "b";
}

function Head({ r }: { r: AnalysisResult }) {
  return (
    <div>
      <p className="font-bold text-slate-800">{r.product_name}</p>
      <div className="mt-1 flex flex-wrap items-center gap-2">
        <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${verdictStyle[r.verdict]}`}>
          {r.verdict}
        </span>
        <span className="text-sm font-bold text-slate-700">
          {r.score}
          <span className="text-xs text-slate-400">/100</span>
        </span>
      </div>
    </div>
  );
}

export default function Compare() {
  const history = getScanHistory();
  const [leftId, setLeftId] = useState(history[0]?.id ?? "");
  const [rightId, setRightId] = useState(history[1]?.id ?? "");

  if (history.length < 2) {
    return (
      <div className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <h2 className="mb-1 text-lg font-bold text-slate-800">Compare products</h2>
        <p className="text-sm text-slate-500">
          Scan at least two products first. Each scan is saved to your history on this device, then you
          can line any two of them up here side by side.
        </p>
      </div>
    );
  }

  const left = history.find((h) => h.id === leftId)?.result ?? history[0].result;
  const right = history.find((h) => h.id === rightId)?.result ?? history[1].result;

  const cell = (side: "a" | "b", w: "a" | "b" | "tie", align: string) =>
    `${align} p-3 ${w === side ? "font-semibold text-emerald-700" : "text-slate-700"}`;

  const scoreW = winner(left.score, right.score, "high");

  return (
    <div className="space-y-4">
      <div className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <h2 className="mb-1 text-lg font-bold text-slate-800">Compare products</h2>
        <p className="mb-4 text-sm text-slate-500">
          Pick two scans. The healthier value in each row is highlighted (more protein/fiber, less
          sugar/saturated fat/sodium). Values are per serving from each scan.
        </p>
        <div className="grid grid-cols-2 gap-3">
          <select
            value={leftId}
            onChange={(e) => setLeftId(e.target.value)}
            className="w-full rounded-lg border border-slate-300 p-2 text-sm focus:border-emerald-500 focus:outline-none"
          >
            {history.map((h) => (
              <option key={h.id} value={h.id} disabled={h.id === rightId}>
                {h.result.product_name} · {h.result.score}/100
              </option>
            ))}
          </select>
          <select
            value={rightId}
            onChange={(e) => setRightId(e.target.value)}
            className="w-full rounded-lg border border-slate-300 p-2 text-sm focus:border-emerald-500 focus:outline-none"
          >
            {history.map((h) => (
              <option key={h.id} value={h.id} disabled={h.id === leftId}>
                {h.result.product_name} · {h.result.score}/100
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="overflow-hidden rounded-2xl bg-white shadow-sm ring-1 ring-slate-200">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100 align-top">
              <th className="w-2/5 p-3 text-left">
                <Head r={left} />
              </th>
              <th className="p-3 text-center text-[10px] uppercase tracking-wide text-slate-300">vs</th>
              <th className="w-2/5 p-3 text-right">
                <Head r={right} />
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            <tr>
              <td className={cell("a", scoreW, "text-left")}>{left.score}/100</td>
              <td className="p-3 text-center text-xs text-slate-400">Overall score</td>
              <td className={cell("b", scoreW, "text-right")}>{right.score}/100</td>
            </tr>
            {METRICS.map((m) => {
              const a = left.serving_nutrition[m.key];
              const b = right.serving_nutrition[m.key];
              const w = winner(a, b, m.better);
              return (
                <tr key={m.key}>
                  <td className={cell("a", w, "text-left")}>
                    {round1(a)} {m.unit}
                  </td>
                  <td className="p-3 text-center text-xs text-slate-400">{m.label}</td>
                  <td className={cell("b", w, "text-right")}>
                    {round1(b)} {m.unit}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="px-1 text-xs text-slate-400">
        Per-serving numbers come from each scan. “Healthier value” is a simple per-nutrient heuristic,
        not an overall verdict — the score already weighs everything together.
      </p>
    </div>
  );
}
