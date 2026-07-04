import { useState } from "react";
import { askQuestion } from "../api";
import type { AskResponse } from "../types";
import NutrientList from "../components/NutrientList";

export default function Ask() {
  const [question, setQuestion] = useState("");
  const [image, setImage] = useState<File | null>(null);
  const [answer, setAnswer] = useState<AskResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;
    setLoading(true);
    setError(null);
    setAnswer(null);
    try {
      setAnswer(await askQuestion(question, image));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <form onSubmit={run} className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <h2 className="mb-1 text-lg font-bold">Ask about any food</h2>
        <p className="mb-4 text-sm text-slate-500">
          e.g. "What does an apple contain?" or "Is olive oil good for me?"
        </p>
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          rows={3}
          placeholder="Type your food question…"
          className="w-full resize-none rounded-lg border border-slate-300 p-3 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
        />
        <div className="mt-3 flex items-center justify-between">
          <label className="cursor-pointer text-sm text-slate-500 hover:text-emerald-600">
            {image ? `📎 ${image.name}` : "📎 Attach image (optional)"}
            <input
              type="file"
              accept="image/*"
              className="hidden"
              onChange={(e) => setImage(e.target.files?.[0] ?? null)}
            />
          </label>
          <button
            type="submit"
            disabled={loading || !question.trim()}
            className="rounded-lg bg-emerald-600 px-5 py-2 font-semibold text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? "Thinking…" : "Ask"}
          </button>
        </div>
        {error && <p className="mt-3 rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}
      </form>

      {answer && (
        <div className="space-y-4 rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
          {answer.food_name && (
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-bold">{answer.food_name}</h3>
              {answer.is_natural_food && (
                <span className="rounded bg-sky-100 px-2 py-0.5 text-xs text-sky-700">Natural food</span>
              )}
            </div>
          )}
          <p className="whitespace-pre-line text-slate-700">{answer.answer}</p>

          {answer.benefits.length > 0 && (
            <div>
              <h4 className="font-semibold text-slate-700">Benefits</h4>
              <ul className="mt-1 space-y-1 text-sm">
                {answer.benefits.map((b, i) => (
                  <li key={i} className="flex gap-2"><span>✅</span><span>{b}</span></li>
                ))}
              </ul>
            </div>
          )}

          {answer.nutrients.length > 0 && (
            <div>
              <h4 className="mb-2 font-semibold text-slate-700">Key nutrients</h4>
              <NutrientList nutrients={answer.nutrients} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
