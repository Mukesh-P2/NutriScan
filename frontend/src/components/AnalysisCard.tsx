import { useState } from "react";
import type { AnalysisResult, FoodType, ProductLookup, Verdict } from "../types";
import { lookupBarcode } from "../api";
import { downloadSummary, shareResult } from "../shareResult";
import NutrientList from "./NutrientList";
import ProductLookupCard from "./ProductLookupCard";
import ConsumePanel from "./ConsumePanel";

const verdictStyle: Record<Verdict, string> = {
  healthy: "bg-emerald-100 text-emerald-800",
  moderate: "bg-amber-100 text-amber-800",
  unhealthy: "bg-rose-100 text-rose-800",
};

function VegDot({ type }: { type: FoodType }) {
  if (type === "unknown") return null;
  const veg = type === "veg";
  const color = veg ? "border-green-600 text-green-600" : "border-red-600 text-red-600";
  return (
    <span className={`inline-flex items-center gap-1 rounded border px-2 py-0.5 text-xs font-semibold ${color}`}>
      <span className={`inline-block h-2.5 w-2.5 rounded-full ${veg ? "bg-green-600" : "bg-red-600"}`} />
      {veg ? "Veg" : "Non-veg"}
    </span>
  );
}

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
  const [dbProduct, setDbProduct] = useState<ProductLookup | null>(null);
  const [dbLoading, setDbLoading] = useState(false);
  const [dbError, setDbError] = useState<string | null>(null);
  const [shareMsg, setShareMsg] = useState<string | null>(null);

  // Auto cross-check attached by the backend (ScanResponse.barcode_lookup). When present we show
  // it inline and skip the manual "look up barcode" button.
  const auto = result.barcode_lookup && result.barcode_lookup.found ? result.barcode_lookup : null;
  const crossCheck = dbProduct ?? auto;

  async function onShare() {
    const outcome = await shareResult(result);
    setShareMsg(
      outcome === "shared"
        ? "Shared."
        : outcome === "copied"
          ? "Copied to clipboard."
          : "Couldn't share — try Download.",
    );
  }

  async function lookUp() {
    if (!result.barcode) return;
    setDbLoading(true);
    setDbError(null);
    try {
      setDbProduct(await lookupBarcode(result.barcode));
    } catch (e) {
      setDbError(e instanceof Error ? e.message : "Lookup failed.");
    } finally {
      setDbLoading(false);
    }
  }

  return (
    <>
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

      <div className="flex flex-wrap items-center gap-2">
        <button
          onClick={onShare}
          className="rounded-lg bg-slate-100 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-200"
        >
          🔗 Share / copy
        </button>
        <button
          onClick={() => downloadSummary(result)}
          className="rounded-lg bg-slate-100 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-200"
        >
          ⬇ Download .txt
        </button>
        {shareMsg && <span className="text-xs text-emerald-600">{shareMsg}</span>}
      </div>

      {(result.food_type !== "unknown" || result.allergens.length > 0 || result.diet_tags.length > 0) && (
        <div className="flex flex-wrap items-center gap-2">
          <VegDot type={result.food_type} />
          {result.allergens.map((a) => (
            <span key={a} className="rounded-full bg-rose-100 px-2.5 py-0.5 text-xs font-medium text-rose-700">
              ⚠️ {a}
            </span>
          ))}
          {result.diet_tags
            .filter((d) => d.compatible)
            .map((d) => (
              <span key={d.name} className="rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-medium text-emerald-700">
                ✓ {d.name}
              </span>
            ))}
          {result.diet_tags
            .filter((d) => !d.compatible)
            .map((d) => (
              <span key={d.name} className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-400 line-through">
                {d.name}
              </span>
            ))}
        </div>
      )}

      {result.allergens.length === 0 && result.has_ingredients && (
        <p className="text-xs text-slate-400">No major allergens detected in the listed ingredients.</p>
      )}

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

      <ConsumePanel
        productName={result.product_name}
        verdict={result.verdict}
        score={result.score}
        nutrition={result.serving_nutrition}
      />

      {result.barcode && !dbProduct && !auto && (
        <div className="border-t border-slate-100 pt-4">
          <button
            onClick={lookUp}
            disabled={dbLoading}
            className="rounded-lg bg-slate-100 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-200 disabled:opacity-50"
          >
            {dbLoading ? "Looking up…" : "🔎 Look up barcode in food database"}
          </button>
          <p className="mt-1 text-xs text-slate-400">
            Cross-check with Open Food Facts. Your scanned label stays the source of truth — database
            data can differ by country or be out of date.
          </p>
          {dbError && <p className="mt-2 rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{dbError}</p>}
        </div>
      )}
    </div>

    {crossCheck && (
      <div className="mt-4">
        <p className="mb-2 text-sm font-semibold text-slate-500">
          Database cross-check{crossCheck === auto ? " · auto" : ""}
        </p>
        <ProductLookupCard product={crossCheck} />
      </div>
    )}
    </>
  );
}
