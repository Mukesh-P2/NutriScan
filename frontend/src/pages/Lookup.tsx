import { useState } from "react";
import { lookupBarcode, searchProducts } from "../api";
import type { ProductLookup, ProductSummary } from "../types";
import ProductLookupCard from "../components/ProductLookupCard";

type Mode = "barcode" | "name";

export default function Lookup() {
  const [mode, setMode] = useState<Mode>("name");
  const [query, setQuery] = useState("");
  const [country, setCountry] = useState("");
  const [results, setResults] = useState<ProductSummary[]>([]);
  const [product, setProduct] = useState<ProductLookup | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function openBarcode(barcode: string) {
    setLoading(true);
    setError(null);
    setProduct(null);
    try {
      setProduct(await lookupBarcode(barcode, country.trim() || undefined));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lookup failed.");
    } finally {
      setLoading(false);
    }
  }

  async function run(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    if (mode === "barcode") return openBarcode(query.trim());

    setLoading(true);
    setError(null);
    setResults([]);
    setProduct(null);
    try {
      const res = await searchProducts(query.trim(), country.trim() || undefined);
      setResults(res.results);
      if (res.results.length === 0) setError("No products matched. Try a different name or scan the label.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Search failed.");
    } finally {
      setLoading(false);
    }
  }

  const tabClass = (m: Mode) =>
    `rounded-md px-4 py-1.5 text-sm font-medium ${mode === m ? "bg-white text-emerald-700 shadow-sm" : "text-slate-500"}`;

  return (
    <div className="space-y-6">
      <div className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <h2 className="mb-1 text-lg font-bold">Look up a product</h2>
        <p className="mb-4 text-sm text-slate-500">
          Search the Open Food Facts database by name or barcode. Because data varies by country and
          changes over time, always confirm against the label on your product.
        </p>

        <div className="mb-4 inline-flex gap-1 rounded-lg bg-slate-100 p-1">
          <button type="button" onClick={() => setMode("name")} className={tabClass("name")}>By name</button>
          <button type="button" onClick={() => setMode("barcode")} className={tabClass("barcode")}>By barcode</button>
        </div>

        <form onSubmit={run} className="space-y-3">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            inputMode={mode === "barcode" ? "numeric" : "text"}
            placeholder={mode === "barcode" ? "Enter barcode digits, e.g. 3017620422003" : "Product name, e.g. Parle-G biscuits"}
            className="w-full rounded-lg border border-slate-300 p-2.5 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          />
          <div className="flex items-center gap-3">
            <input
              value={country}
              onChange={(e) => setCountry(e.target.value)}
              placeholder="Country (optional) — e.g. India"
              className="w-full rounded-lg border border-slate-300 p-2.5 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="shrink-0 rounded-lg bg-emerald-600 px-5 py-2.5 font-semibold text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "…" : mode === "barcode" ? "Look up" : "Search"}
            </button>
          </div>
          <p className="text-xs text-slate-400">
            Set a country to bias results toward that region's version of the product.
          </p>
        </form>

        {error && <p className="mt-3 rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}
      </div>

      {/* Search results — pick the one whose brand/region matches what you have */}
      {results.length > 0 && !product && (
        <div className="space-y-2">
          <p className="text-sm text-slate-500">Pick the match closest to your product:</p>
          {results.map((r) => (
            <button
              key={r.barcode}
              onClick={() => openBarcode(r.barcode)}
              className="flex w-full items-center gap-3 rounded-xl bg-white p-3 text-left shadow-sm ring-1 ring-slate-200 hover:ring-emerald-300"
            >
              {r.image_url ? (
                <img src={r.image_url} alt="" className="h-12 w-12 rounded object-contain ring-1 ring-slate-100" />
              ) : (
                <div className="flex h-12 w-12 items-center justify-center rounded bg-slate-100 text-slate-300">🍫</div>
              )}
              <div className="min-w-0">
                <p className="truncate font-medium text-slate-800">{r.product_name || "Unnamed product"}</p>
                <p className="truncate text-xs text-slate-500">
                  {[r.brands, r.countries.slice(0, 2).join(", ")].filter(Boolean).join(" · ")}
                </p>
              </div>
            </button>
          ))}
        </div>
      )}

      {product && (
        <div className="space-y-3">
          {results.length > 0 && (
            <button onClick={() => setProduct(null)} className="text-sm font-semibold text-emerald-600 hover:underline">
              ← Back to results
            </button>
          )}
          <ProductLookupCard product={product} />
        </div>
      )}
    </div>
  );
}
