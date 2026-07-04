import type { AnalysisResult, Verdict } from "../types";
import NutrientList from "./NutrientList";

const verdictStyle: Record<Verdict, string> = {
  healthy: "bg-emerald-100 text-emerald-800",
  moderate: "bg-amber-100 text-amber-800",
  unhealthy: "bg-rose-100 text-rose-800",
};

function List({ title, items, marker }: { title: string; items: string[]; marker: string }) {
  if (!items.length) return null;
  return (
    <div>
      <h4 className="font-semibold text-slate-700">{title}</h4>
      <ul className="mt-1 space-y-1 text-sm">
        {items.map((it, i) => (
          <li key={i} className="flex gap-2">
            <span>{marker}</span>
            <span>{it}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function AnalysisCard({ result }: { result: AnalysisResult }) {
  return (
    <div className="space-y-5 rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold">{result.product_name}</h2>
          {result.barcode && <p className="text-xs text-slate-400">Barcode: {result.barcode}</p>}
          {!result.has_ingredients && (
            <span className="mt-1 inline-block rounded bg-sky-100 px-2 py-0.5 text-xs text-sky-700">
              Natural / whole food
            </span>
          )}
        </div>
        <div className="text-right">
          <span className={`rounded-full px-3 py-1 text-sm font-semibold uppercase ${verdictStyle[result.verdict]}`}>
            {result.verdict}
          </span>
          <div className="mt-1 text-2xl font-bold text-slate-700">{result.score}<span className="text-sm text-slate-400">/100</span></div>
        </div>
      </div>

      <p className="text-slate-600">{result.summary}</p>

      {result.missing_info.length > 0 && (
        <div className="rounded-lg bg-amber-50 p-3 text-sm text-amber-800">
          Missing info: {result.missing_info.join(", ")}. Add another photo (e.g. the ingredients or nutrition panel) for a fuller analysis.
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-3">
        <List title="Pros" items={result.pros} marker="✅" />
        <List title="Cons" items={result.cons} marker="⚠️" />
        <List title="Tips" items={result.tips} marker="💡" />
      </div>

      {result.key_nutrients.length > 0 && (
        <div>
          <h4 className="mb-2 font-semibold text-slate-700">Daily needs coverage</h4>
          <NutrientList nutrients={result.key_nutrients} />
          <p className="mt-2 text-xs text-slate-400">{result.daily_context_note}</p>
        </div>
      )}

      <div className="flex flex-wrap gap-4 rounded-lg bg-slate-50 p-3 text-sm">
        <div><span className="text-slate-400">Recommended serving:</span> <b>{result.recommended_serving}</b></div>
        <div><span className="text-slate-400">Max per day:</span> <b>{result.max_per_day}</b></div>
      </div>

      {result.whole_pack_context && (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-900">
          <div className="mb-1 flex flex-wrap gap-x-4 font-semibold">
            <span>📦 Whole-pack analysis</span>
            {result.total_weight && <span className="font-normal text-emerald-700">Pack: {result.total_weight}</span>}
            {result.servings_in_pack != null && (
              <span className="font-normal text-emerald-700">≈ {result.servings_in_pack} servings</span>
            )}
          </div>
          <p>{result.whole_pack_context}</p>
        </div>
      )}
    </div>
  );
}
