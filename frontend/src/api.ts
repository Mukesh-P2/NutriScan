import type { AnalysisResult, AskResponse, ProductLookup, ProductSearchResults } from "./types";
import { tokenStore } from "./auth";

async function parseError(res: Response): Promise<string> {
  try {
    const data = await res.json();
    if (typeof data.detail === "string") return data.detail;
    return JSON.stringify(data.detail ?? data);
  } catch {
    return `Request failed (${res.status})`;
  }
}

// Optional bearer token — when present the backend personalizes results to the user.
function maybeAuth(): HeadersInit {
  const token = tokenStore.get();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function analyzeImages(files: File[], totalWeight?: string): Promise<AnalysisResult> {
  const form = new FormData();
  for (const file of files) form.append("images", file);
  if (totalWeight && totalWeight.trim()) form.append("total_weight", totalWeight.trim());

  const res = await fetch("/api/analyze", { method: "POST", body: form, headers: maybeAuth() });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function askQuestion(question: string, image?: File | null): Promise<AskResponse> {
  const form = new FormData();
  form.append("question", question);
  if (image) form.append("image", image);

  const res = await fetch("/api/ask", { method: "POST", body: form, headers: maybeAuth() });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function lookupBarcode(barcode: string, country?: string): Promise<ProductLookup> {
  const qs = country ? `?country=${encodeURIComponent(country)}` : "";
  const res = await fetch(`/api/lookup/barcode/${encodeURIComponent(barcode)}${qs}`);
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function searchProducts(q: string, country?: string): Promise<ProductSearchResults> {
  const params = new URLSearchParams({ q });
  if (country) params.set("country", country);
  const res = await fetch(`/api/lookup/search?${params}`);
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}
