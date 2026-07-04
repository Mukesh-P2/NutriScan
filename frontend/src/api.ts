import type { AnalysisResult, AskResponse } from "./types";

async function parseError(res: Response): Promise<string> {
  try {
    const data = await res.json();
    if (typeof data.detail === "string") return data.detail;
    return JSON.stringify(data.detail ?? data);
  } catch {
    return `Request failed (${res.status})`;
  }
}

export async function analyzeImages(files: File[], totalWeight?: string): Promise<AnalysisResult> {
  const form = new FormData();
  for (const file of files) form.append("images", file);
  if (totalWeight && totalWeight.trim()) form.append("total_weight", totalWeight.trim());

  const res = await fetch("/api/analyze", { method: "POST", body: form });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function askQuestion(question: string, image?: File | null): Promise<AskResponse> {
  const form = new FormData();
  form.append("question", question);
  if (image) form.append("image", image);

  const res = await fetch("/api/ask", { method: "POST", body: form });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}
