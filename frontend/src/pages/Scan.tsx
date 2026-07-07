import { useEffect, useState } from "react";
import { analyzeImages } from "../api";
import type { AnalysisResult } from "../types";
import AnalysisCard from "../components/AnalysisCard";
import ImagePicker from "../components/ImagePicker";
import ErrorNotice from "../components/ErrorNotice";
import { addScan, clearScanHistory, getScanHistory, removeScan, type ScanHistoryItem } from "../scanHistory";

export default function Scan() {
  const [files, setFiles] = useState<File[]>([]);
  const [totalWeight, setTotalWeight] = useState("");
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<ScanHistoryItem[]>([]);

  useEffect(() => {
    setHistory(getScanHistory());
  }, []);

  async function run() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await analyzeImages(files, totalWeight);
      setResult(res);
      setHistory(addScan(res));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  function reopen(item: ScanHistoryItem) {
    setResult(item.result);
    setError(null);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  return (
    <div className="space-y-6">
      <div className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <h2 className="mb-1 text-lg font-bold">Scan a food product</h2>
        <p className="mb-4 text-sm text-slate-500">
          Snap or upload the label. Add multiple photos if one image can't capture all the ingredients.
        </p>
        <ImagePicker files={files} onChange={setFiles} />

        <div className="mt-4">
          <label className="block text-sm font-medium text-slate-600">
            Total pack weight <span className="font-normal text-slate-400">(optional)</span>
          </label>
          <input
            type="text"
            value={totalWeight}
            onChange={(e) => setTotalWeight(e.target.value)}
            placeholder="e.g. 90g or 250ml"
            className="mt-1 w-40 rounded-lg border border-slate-300 p-2 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          />
          <p className="mt-1 text-xs text-slate-400">
            Enter the net weight of the whole pack to get whole-pack impact and how much to eat.
          </p>
        </div>

        <button
          onClick={run}
          disabled={loading || files.length === 0}
          className="mt-4 rounded-lg bg-emerald-600 px-5 py-2 font-semibold text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? "Analyzing…" : "Analyze"}
        </button>
        {error && (
          <div className="mt-3">
            <ErrorNotice message={error} onRetry={files.length > 0 ? run : undefined} />
          </div>
        )}
      </div>

      {result && <AnalysisCard result={result} />}

      {history.length > 0 && (
        <div className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="font-semibold text-slate-700">Recent scans</h3>
            <button
              onClick={() => setHistory(clearScanHistory())}
              className="text-xs font-semibold text-slate-400 hover:text-rose-600"
            >
              Clear all
            </button>
          </div>
          <ul className="divide-y divide-slate-100">
            {history.map((h) => (
              <li key={h.id} className="flex items-center justify-between gap-3 py-2 text-sm">
                <button onClick={() => reopen(h)} className="min-w-0 flex-1 truncate text-left hover:text-emerald-700">
                  <span className="font-medium text-slate-700">{h.result.product_name}</span>
                  <span className="ml-2 text-xs text-slate-400">
                    {h.result.verdict} · {h.result.score}/100
                  </span>
                </button>
                <button
                  onClick={() => setHistory(removeScan(h.id))}
                  aria-label="Remove from history"
                  className="shrink-0 text-xs font-semibold text-slate-300 hover:text-rose-600"
                >
                  ✕
                </button>
              </li>
            ))}
          </ul>
          <p className="mt-2 text-xs text-slate-400">
            Saved on this device only. Line any two up in the <b>Compare</b> tab.
          </p>
        </div>
      )}
    </div>
  );
}
