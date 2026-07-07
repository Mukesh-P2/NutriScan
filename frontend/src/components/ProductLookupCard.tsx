import type { ProductLookup } from "../types";
import { servingFromLookup } from "../offNutrition";
import ConsumePanel from "./ConsumePanel";

// Renders a food-database result. Caveats are shown FIRST and prominently — the whole point
// is that this data is a hint to verify, not authoritative (region/formulation can differ).
// `allowConsume` opts into a "log this to today" panel (used on the Lookup tab).
export default function ProductLookupCard({
  product,
  allowConsume = false,
}: {
  product: ProductLookup;
  allowConsume?: boolean;
}) {
  if (!product.found) {
    return (
      <div className="rounded-2xl bg-white p-6 text-sm text-slate-500 shadow-sm ring-1 ring-slate-200">
        No database match{product.barcode ? ` for barcode ${product.barcode}` : ""}. Scan the physical
        label for an accurate analysis.
      </div>
    );
  }

  const consumeNutrition = allowConsume ? servingFromLookup(product) : null;

  return (
    <div className="space-y-4 rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
      {/* Caveats first — accuracy guardrail */}
      {product.caveats.length > 0 && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
          <p className="mb-1 font-semibold">⚠️ Verify before you trust this</p>
          <ul className="list-disc space-y-1 pl-5">
            {product.caveats.map((c, i) => (
              <li key={i}>{c}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="flex items-start gap-4">
        {product.image_url && (
          <img src={product.image_url} alt="" className="h-20 w-20 rounded-lg object-contain ring-1 ring-slate-100" />
        )}
        <div className="min-w-0">
          <h3 className="text-lg font-bold">{product.product_name || "Unnamed product"}</h3>
          {product.brands && <p className="text-sm text-slate-500">{product.brands}</p>}
          {product.barcode && <p className="text-xs text-slate-400">Barcode: {product.barcode}</p>}
        </div>
      </div>

      <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm text-slate-600">
        {product.countries.length > 0 && (
          <span><span className="text-slate-400">Region(s):</span> {product.countries.join(", ")}</span>
        )}
        {product.last_modified && (
          <span><span className="text-slate-400">Data updated:</span> {product.last_modified}</span>
        )}
      </div>

      {product.allergens.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {product.allergens.map((a) => (
            <span key={a} className="rounded-full bg-rose-100 px-2.5 py-0.5 text-xs font-medium text-rose-700">
              ⚠️ {a}
            </span>
          ))}
        </div>
      )}

      {product.ingredients_text && (
        <div>
          <h4 className="font-semibold text-slate-700">Ingredients (per database)</h4>
          <p className="mt-1 text-sm text-slate-600">{product.ingredients_text}</p>
        </div>
      )}

      {product.nutriments.length > 0 && (
        <div>
          <h4 className="mb-1 font-semibold text-slate-700">Nutrition (per 100 g)</h4>
          <ul className="divide-y divide-slate-100">
            {product.nutriments.map((n) => (
              <li key={n.name} className="flex justify-between py-1.5 text-sm">
                <span className="text-slate-600">{n.name}</span>
                <span className="font-medium text-slate-800">{n.amount}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {consumeNutrition && (
        <div className="border-t border-slate-100 pt-4">
          <p className="text-xs text-slate-500">
            Log this from the database values. Numbers are <b>per 100&nbsp;g</b> — set servings to your
            portion in 100&nbsp;g units (e.g. 1.5 = 150&nbsp;g). Always verify against the label.
          </p>
          <ConsumePanel
            productName={product.product_name || "Database product"}
            nutrition={consumeNutrition}
          />
        </div>
      )}

      {product.source_url && (
        <a
          href={product.source_url}
          target="_blank"
          rel="noreferrer"
          className="inline-block text-xs text-emerald-600 hover:underline"
        >
          View on {product.source} ↗
        </a>
      )}
    </div>
  );
}
