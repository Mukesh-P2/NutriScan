// Share / export a scan result as a readable text summary. Uses the native Web Share sheet
// when available (mobile), otherwise copies to the clipboard; plus a .txt download fallback.
import type { AnalysisResult } from "./types";

export function buildSummary(r: AnalysisResult): string {
  const lines: string[] = [];
  lines.push(`NutriScan — ${r.product_name}`);
  lines.push(`Verdict: ${r.verdict.toUpperCase()} · Score: ${r.score}/100`);
  if (r.summary) lines.push("", r.summary);
  if (r.pros.length) lines.push("", "Pros:", ...r.pros.map((p) => `  + ${p}`));
  if (r.cons.length) lines.push("", "Cons:", ...r.cons.map((c) => `  - ${c}`));
  if (r.tips.length) lines.push("", "Tips:", ...r.tips.map((t) => `  * ${t}`));
  if (r.key_nutrients.length) {
    lines.push("", "Per serving:");
    for (const n of r.key_nutrients) {
      lines.push(`  ${n.name}: ${n.amount_per_serving} (${n.percent_of_daily}% DV)`);
    }
  }
  lines.push("", `Serving: ${r.recommended_serving} · Max/day: ${r.max_per_day}`);
  lines.push("", "Shared from NutriScan — AI reads the label; health numbers are computed, not guessed.");
  return lines.join("\n");
}

export type ShareOutcome = "shared" | "copied" | "failed";

export async function shareResult(r: AnalysisResult): Promise<ShareOutcome> {
  const text = buildSummary(r);
  const title = `NutriScan: ${r.product_name}`;
  const nav = navigator as Navigator & { share?: (data: ShareData) => Promise<void> };
  if (nav.share) {
    try {
      await nav.share({ title, text });
      return "shared";
    } catch {
      /* user cancelled or share failed — fall through to clipboard copy */
    }
  }
  try {
    await navigator.clipboard.writeText(text);
    return "copied";
  } catch {
    return "failed";
  }
}

export function downloadSummary(r: AnalysisResult): void {
  const blob = new Blob([buildSummary(r)], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const safe =
    r.product_name.replace(/[^a-z0-9]+/gi, "-").replace(/^-+|-+$/g, "").toLowerCase() || "scan";
  const a = document.createElement("a");
  a.href = url;
  a.download = `nutriscan-${safe}.txt`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
