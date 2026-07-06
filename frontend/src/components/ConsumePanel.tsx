import { useState } from "react";
import { useAuth } from "../AuthContext";
import { logConsumption, previewConsumption } from "../consumption";
import type { ConsumeInput, ConsumptionRecommendation, ServingNutrition, Verdict } from "../types";

const FIT_STYLE: Record<string, string> = {
  good: "border-emerald-200 bg-emerald-50 text-emerald-900",
  ok: "border-amber-200 bg-amber-50 text-amber-900",
  avoid: "border-rose-200 bg-rose-50 text-rose-900",
};

// Which per-nutrient effects are worth surfacing (skip the quiet "ok" ones).
const NOTABLE = new Set(["fills", "completes", "met", "near", "over", "pushes_over"]);
const effectIcon: Record<string, string> = {
  fills: "➕", completes: "🎉", met: "✅", near: "🟡", over: "⚠️", pushes_over: "🔴",
};

export default function ConsumePanel({
  productName,
  verdict,
  score,
  nutrition,
}: {
  productName: string;
  verdict: Verdict;
  score: number;
  nutrition: ServingNutrition;
}) {
  const { user } = useAuth();
  const [servings, setServings] = useState(1);
  const [rec, setRec] = useState<ConsumptionRecommendation | null>(null);
  const [loading, setLoading] = useState(false);
  const [logging, setLogging] = useState(false);
  const [logged, setLogged] = useState<number | null>(null); // achievement % after logging
  const [error, setError] = useState<string | null>(null);

  if (!user) {
    return (
      <div className="border-t border-slate-100 pt-4 text-sm text-slate-500">
        🔒 Log in from the <span className="font-semibold text-emerald-600">Profile</span> tab to record this
        and track it against your daily targets.
      </div>
    );
  }

  const input = (): ConsumeInput => ({
    product_name: productName,
    servings,
    nutrition,
    product_verdict: verdict,
    product_score: score,
  });

  async function check() {
    setLoading(true);
    setError(null);
    setLogged(null);
    try {
      setRec(await previewConsumption(input()));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't check fit.");
    } finally {
      setLoading(false);
    }
  }

  async function consume() {
    setLogging(true);
    setError(null);
    try {
      const prog = await logConsumption(input());
      setLogged(prog.achievement_pct);
      setRec(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't log it.");
    } finally {
      setLogging(false);
    }
  }

  return (
    <div className="space-y-3 border-t border-slate-100 pt-4">
      <div className="flex flex-wrap items-center gap-3">
        <span className="text-sm font-semibold text-slate-700">Eat this?</span>
        <label className="flex items-center gap-1 text-sm text-slate-500">
          Servings
          <input
            type="number"
            min={0.25}
            step={0.25}
            value={servings}
            onChange={(e) => {
              setServings(Math.max(0.25, Number(e.target.value) || 0.25));
              setRec(null);
              setLogged(null);
            }}
            className="w-16 rounded-lg border border-slate-300 p-1.5 focus:border-emerald-500 focus:outline-none"
          />
        </label>
        <button
          onClick={check}
          disabled={loading}
          className="rounded-lg bg-slate-100 px-3 py-1.5 text-sm font-semibold text-slate-700 hover:bg-slate-200 disabled:opacity-50"
        >
          {loading ? "Checking…" : "Check today's fit"}
        </button>
      </div>

      {error && <p className="rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}

      {logged !== null && (
        <p className="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-800">
          ✓ Added to today. You're now at <b>{logged}%</b> of your daily targets — see the <b>Today</b> tab.
        </p>
      )}

      {rec && (
        <div className={`space-y-3 rounded-xl border p-4 ${FIT_STYLE[rec.daily_fit]}`}>
          {!rec.targets_complete && (
            <p className="rounded-lg bg-white/60 p-2 text-xs">
              Using generic targets — complete your profile for advice tuned to you.
            </p>
          )}
          <p className="font-semibold">{rec.fit_headline}</p>
          <p className="text-sm">{rec.general_message}</p>

          <ul className="space-y-1 text-sm">
            {rec.effects
              .filter((e) => NOTABLE.has(e.status))
              .map((e) => (
                <li key={e.name} className="flex gap-2">
                  <span>{effectIcon[e.status] ?? "•"}</span>
                  <span>{e.message}</span>
                </li>
              ))}
          </ul>

          <p className="text-xs opacity-80">
            Daily progress would go {rec.current_achievement_pct}% → <b>{rec.projected_achievement_pct}%</b>
          </p>

          <button
            onClick={consume}
            disabled={logging}
            className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
          >
            {logging ? "Adding…" : `✓ I ate this (${servings} serving${servings === 1 ? "" : "s"})`}
          </button>
        </div>
      )}
    </div>
  );
}
