// Consumption-tracking API calls (all require auth — reuse authFetch from auth.ts).
import { authFetch } from "./auth";
import type {
  ConsumeInput,
  ConsumptionRecommendation,
  DailyProgress,
  DaySummary,
} from "./types";

const JSON_HEADERS = { "Content-Type": "application/json" };

export async function previewConsumption(input: ConsumeInput): Promise<ConsumptionRecommendation> {
  return (
    await authFetch("/api/consumption/preview", {
      method: "POST",
      headers: JSON_HEADERS,
      body: JSON.stringify(input),
    })
  ).json();
}

export async function logConsumption(input: ConsumeInput): Promise<DailyProgress> {
  return (
    await authFetch("/api/consumption/log", {
      method: "POST",
      headers: JSON_HEADERS,
      body: JSON.stringify(input),
    })
  ).json();
}

export async function fetchToday(): Promise<DailyProgress> {
  return (await authFetch("/api/consumption/today")).json();
}

export async function deleteConsumption(id: number): Promise<DailyProgress> {
  return (await authFetch(`/api/consumption/${id}`, { method: "DELETE" })).json();
}

export async function fetchHistory(days = 7): Promise<{ days: DaySummary[] }> {
  return (await authFetch(`/api/consumption/history?days=${days}`)).json();
}
