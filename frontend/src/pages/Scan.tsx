import { useState } from "react";
import { analyzeImages } from "../api";
import type { AnalysisResult } from "../types";
import AnalysisCard from "../components/AnalysisCard";
import ImagePicker from "../components/ImagePicker";

export default function Scan() {
  const [files, setFiles] = useState<File[]>([]);
  const [totalWeight, setTotalWeight] = useState("");
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      setResult(await analyzeImages(files, totalWeight));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
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
        {error && <p className="mt-3 rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}
      </div>

      {result && <AnalysisCard result={result} />}
    </div>
  );
}
