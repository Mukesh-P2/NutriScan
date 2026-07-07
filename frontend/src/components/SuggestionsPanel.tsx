import { useState } from "react";
import { fetchSuggestions } from "../consumption";
import type { FoodSuggestions } from "../types";
import ErrorNotice from "./ErrorNotice";

// "What should I eat next?" — on demand, asks the backend for foods that fill TODAY's remaining
// gaps. The gaps are computed deterministically server-side; the AI only picks the foods.
export default function SuggestionsPanel() {
  const [data, setData] = useState<FoodSuggestions | null>(null);
  const [country, setCountry] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setLoading(true);
    setError(null);
    try {
      setData(await fetchSuggestions(country));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't get suggestions.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4 rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="font-semibold text-slate-700">What should I eat next?</h3>
          <p className="text-xs text-slate-400">
            AI foods to fill what's left of today — your target numbers stay exact.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <input
            value={country}
            onChange={(e) => setCountry(e.target.value)}
            placeholder="Country (optional)"
            className="w-36 rounded-lg border border-slate-300 p-1.5 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          />
          <button
            onClick={run}
            disabled={loading}
            className="rounded-lg bg-emerald-600 px-4 py-1.5 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
          >
            {loading ? "Thinking…" : data ? "Refresh" : "Suggest foods"}
          </button>
        </div>
      </div>

      {error && <ErrorNotice message={error} onRetry={run} />}

      {data && (
        <div className="space-y-4">
          <p className="text-sm text-slate-600">{data.summary}</p>

          {data.focus_nutrients.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {data.focus_nutrients.map((n) => (
                <span key={n} className="rounded-full bg-sky-100 px-2.5 py-0.5 text-xs font-medium text-sky-700">
                  {n}
                </span>
              ))}
            </div>
          )}

          {data.suggestions.length > 0 && (
            <ul className="grid gap-3 sm:grid-cols-2">
              {data.suggestions.map((s, i) => (
                <li key={i} className="rounded-xl border border-slate-200 p-3">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-semibold text-slate-800">{s.food}</span>
                    <span
                      className={`shrink-0 rounded border px-1.5 py-0.5 text-[10px] font-semibold ${
                        s.is_veg ? "border-green-600 text-green-600" : "border-red-600 text-red-600"
                      }`}
                    >
                      {s.is_veg ? "Veg" : "Non-veg"}
                    </span>
                  </div>
                  {s.serving_idea && <p className="mt-0.5 text-xs text-slate-500">{s.serving_idea}</p>}
                  {s.why && <p className="mt-1 text-sm text-slate-600">{s.why}</p>}
                  {s.fills.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {s.fills.map((f) => (
                        <span key={f} className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-medium text-emerald-700">
                          + {f}
                        </span>
                      ))}
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}

          {data.cautions.length > 0 && (
            <div className="rounded-lg bg-amber-50 p-3 text-sm text-amber-800">
              <p className="mb-1 font-semibold">Watch out</p>
              <ul className="list-disc space-y-0.5 pl-5">
                {data.cautions.map((c, i) => (
                  <li key={i}>{c}</li>
                ))}
              </ul>
            </div>
          )}

          {data.disclaimer && <p className="text-xs text-slate-400">{data.disclaimer}</p>}
        </div>
      )}
    </div>
  );
}
