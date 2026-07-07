import { useEffect, useState } from "react";
import { fetchHealth } from "../api";
import type { Health } from "../types";

// Tiny header badge showing the backend's active Gemini model chain (from /health).
// Green = key configured & a model chain is active; amber = key missing; gray = backend down.
export default function HealthBadge() {
  const [health, setHealth] = useState<Health | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let alive = true;
    fetchHealth()
      .then((h) => alive && setHealth(h))
      .catch(() => alive && setFailed(true));
    return () => {
      alive = false;
    };
  }, []);

  const base =
    "hidden items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium sm:inline-flex";

  if (failed) {
    return (
      <span title="Backend unreachable" className={`${base} bg-slate-100 text-slate-400`}>
        <span className="h-1.5 w-1.5 rounded-full bg-slate-400" /> offline
      </span>
    );
  }
  if (!health) return null;

  const ok = health.gemini_configured && health.model_chain.length > 0;
  return (
    <span
      title={
        ok
          ? `Active model chain: ${health.model_chain.join(" → ")}`
          : "Set GEMINI_API_KEY on the backend to enable AI features"
      }
      className={`${base} bg-slate-100 text-slate-500`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${ok ? "bg-emerald-500" : "bg-amber-500"}`} />
      {ok ? health.model_chain[0] : "AI key missing"}
    </span>
  );
}
